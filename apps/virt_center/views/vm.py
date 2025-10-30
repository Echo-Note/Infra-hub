#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟机管理视图
"""

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from apps.common.core.modelset import BaseModelSet
from apps.common.core.response import ApiResponse
from apps.common.swagger.utils import get_default_response_schema
from apps.virt_center.decorators import record_operation
from apps.virt_center.filters import VirtualMachineFilter
from apps.virt_center.models import VirtualMachine
from apps.virt_center.serializers import (
    VirtualMachineDetailSerializer,
    VirtualMachineListSerializer,
    VirtualMachineSerializer,
    VMOperationSerializer,
)


class VirtualMachineViewSet(BaseModelSet):
    """虚拟机管理视图集"""

    queryset = VirtualMachine.objects.select_related("platform", "host").all()
    serializer_class = VirtualMachineSerializer
    list_serializer_class = VirtualMachineListSerializer
    ordering_fields = ["created_time", "updated_time", "name", "cpu_usage_percent", "memory_usage_percent"]
    filterset_class = VirtualMachineFilter

    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == "list":
            return VirtualMachineListSerializer
        elif self.action == "retrieve":
            return VirtualMachineDetailSerializer
        return VirtualMachineSerializer

    @extend_schema(responses=get_default_response_schema())
    def retrieve(self, request, *args, **kwargs):
        """获取虚拟机详情（包括磁盘、网络、快照）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ApiResponse(data=serializer.data)

    @extend_schema(
        request=VMOperationSerializer,
        responses=get_default_response_schema(),
    )
    @action(methods=["POST"], detail=True, url_path="operate")
    @record_operation("operate", "vm")
    def operate_vm(self, request, *args, **kwargs):
        """执行虚拟机操作（开机、关机、重启等）"""
        vm = self.get_object()
        serializer = VMOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        operation = serializer.validated_data["operation"]
        force = serializer.validated_data.get("force", False)

        try:
            from apps.virt_center.services.vsphere_client import get_vsphere_client

            client = get_vsphere_client(vm.platform)

            with client:
                # 根据操作类型执行相应操作
                if operation == "power_on":
                    result = client.power_on_vm(vm.mo_ref)
                    message = "虚拟机已开机"
                elif operation == "power_off":
                    if force:
                        result = client.power_off_vm(vm.mo_ref)
                        message = "虚拟机已强制关机"
                    else:
                        result = client.shutdown_guest(vm.mo_ref)
                        message = "已发送关机信号"
                elif operation == "suspend":
                    result = client.suspend_vm(vm.mo_ref)
                    message = "虚拟机已挂起"
                elif operation == "reset":
                    result = client.reset_vm(vm.mo_ref)
                    message = "虚拟机已重启"
                elif operation == "shutdown":
                    result = client.shutdown_guest(vm.mo_ref)
                    message = "已发送关闭客户机信号"
                elif operation == "reboot":
                    result = client.reboot_guest(vm.mo_ref)
                    message = "已发送重启客户机信号"
                else:
                    return ApiResponse(code=1001, msg=_("Invalid operation type"))

                return ApiResponse(
                    data={
                        "operation": operation,
                        "vm_name": vm.name,
                        "result": result,
                        "message": message,
                    },
                    msg=_("Operation successful"),
                )

        except Exception as e:
            return ApiResponse(
                code=1001,
                msg=_("Operation failed"),
                data={"error": str(e), "operation": operation},
            )

    @extend_schema(responses=get_default_response_schema())
    @action(methods=["POST"], detail=True, url_path="sync")
    @record_operation("sync_data", "vm")
    def sync_vm(self, request, *args, **kwargs):
        """同步单个虚拟机的数据"""
        vm = self.get_object()

        try:
            from apps.virt_center.tasks import sync_vm_detail

            # 异步执行同步任务
            result = sync_vm_detail.delay(str(vm.id))

            return ApiResponse(
                data={
                    "task_id": result.id,
                    "vm_id": str(vm.id),
                    "vm_name": vm.name,
                    "message": "同步任务已启动",
                },
                msg=_("Sync task started"),
            )

        except Exception as e:
            return ApiResponse(
                code=1001,
                msg=_("Failed to start sync task"),
                data={"error": str(e)},
            )

    @extend_schema(responses=get_default_response_schema())
    @action(methods=["GET"], detail=False, url_path="statistics")
    def statistics(self, request):
        """获取虚拟机统计数据"""
        queryset = self.filter_queryset(self.get_queryset())

        total_count = queryset.count()
        running_count = queryset.filter(power_state=VirtualMachine.PowerState.POWERED_ON).count()
        stopped_count = queryset.filter(power_state=VirtualMachine.PowerState.POWERED_OFF).count()
        suspended_count = queryset.filter(power_state=VirtualMachine.PowerState.SUSPENDED).count()
        template_count = queryset.filter(is_template=True).count()

        # 操作系统统计
        os_stats = {}
        for os_type in VirtualMachine.OSType.choices:
            count = queryset.filter(os_type=os_type[0]).count()
            if count > 0:
                os_stats[os_type[1]] = count

        # 资源统计
        from django.db.models import Avg, Sum

        resource_stats = queryset.aggregate(
            total_cpu=Sum("cpu_count"),
            total_memory_mb=Sum("memory_mb"),
            total_disk_gb=Sum("total_disk_gb"),
            avg_cpu_usage=Avg("cpu_usage_percent"),
            avg_memory_usage=Avg("memory_usage_percent"),
        )

        return ApiResponse(
            data={
                "total_count": total_count,
                "running_count": running_count,
                "stopped_count": stopped_count,
                "suspended_count": suspended_count,
                "template_count": template_count,
                "os_stats": os_stats,
                "resource_stats": {
                    "total_cpu": resource_stats["total_cpu"] or 0,
                    "total_memory_gb": round((resource_stats["total_memory_mb"] or 0) / 1024, 2),
                    "total_disk_gb": resource_stats["total_disk_gb"] or 0,
                    "avg_cpu_usage": round(resource_stats["avg_cpu_usage"] or 0, 2),
                    "avg_memory_usage": round(resource_stats["avg_memory_usage"] or 0, 2),
                },
            }
        )
