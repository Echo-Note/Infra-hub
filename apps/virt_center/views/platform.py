#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
平台管理视图
"""

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from apps.common.core.modelset import BaseModelSet
from apps.common.core.response import ApiResponse
from apps.common.swagger.utils import get_default_response_schema
from apps.virt_center.decorators import record_operation
from apps.virt_center.filters import PlatformFilter
from apps.virt_center.models import Platform, PlatformCredential
from apps.virt_center.serializers import PlatformCredentialSerializer, PlatformSerializer
from apps.virt_center.tasks import sync_all_platform_data


class PlatformViewSet(BaseModelSet):
    """平台管理视图集"""

    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    ordering_fields = ["created_time", "updated_time", "name"]
    # search_fields 会覆盖 SearchFieldsAction 的 search_fields 方法，需要移除
    # search_fields = ["name", "host", "region", "datacenter"]

    # 搜索功能由 filterset_class 提供
    # filterset_fields = {
    #     "platform_type": ["exact"],
    #     "status": ["exact"],
    #     "is_active": ["exact"],
    #     "region": ["exact", "icontains"],
    # }
    filterset_class = PlatformFilter

    @extend_schema(responses=get_default_response_schema())
    @action(methods=["POST"], detail=True, url_path="test-connection")
    @record_operation("other", "platform")
    def test_connection(self, request, *args, **kwargs):
        """测试平台连接"""
        platform = self.get_object()

        try:
            from apps.virt_center.services.vsphere_client import get_vsphere_client

            client = get_vsphere_client(platform)

            with client:
                about_info = client.get_about_info()

                # 更新平台状态
                platform.status = Platform.Status.CONNECTED
                platform.save(update_fields=["status", "updated_time"])

                return ApiResponse(
                    data={
                        "connected": True,
                        "platform_info": about_info,
                        "message": "连接成功",
                    },
                    msg=_("Platform connection successful"),
                )

        except Exception as e:
            # 更新平台状态为异常
            platform.status = Platform.Status.ERROR
            platform.save(update_fields=["status", "updated_time"])

            # 根据错误类型提供用户友好的提示信息
            error_msg = str(e)
            detail_msg = "连接失败，请检查以下内容：\n"

            # 常见错误类型及处理建议
            if "authentication" in error_msg.lower() or "login" in error_msg.lower():
                detail_msg += "1. 请确认用户名和密码是否正确\n2. 检查账户是否被锁定或过期"
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                detail_msg += "1. 检查主机地址和端口是否正确\n2. 确认网络连接是否正常\n3. 检查防火墙是否阻止了连接"
            elif "certificate" in error_msg.lower() or "ssl" in error_msg.lower():
                detail_msg += "1. SSL 证书验证失败，建议关闭 SSL 验证\n2. 或者为 vCenter 配置有效的 SSL 证书"
            elif "connect" in error_msg.lower() or "refused" in error_msg.lower():
                detail_msg += (
                    "1. 检查主机地址是否正确\n2. 确认 vCenter/ESXi 服务是否正常运行\n3. 检查端口号（默认 443）是否正确"
                )
            elif "not found" in error_msg.lower() or "404" in error_msg:
                detail_msg += "1. 检查主机地址格式是否正确\n2. 确认 vCenter/ESXi 服务是否可访问"
            else:
                detail_msg += (
                    f"1. 检查主机地址、端口、用户名和密码是否正确\n2. 确认网络连接正常\n3. 错误详情：{error_msg}"
                )

            return ApiResponse(
                code=1001,
                msg=_("Platform connection failed"),
                detail=detail_msg,
                data={"connected": False, "error": error_msg},
            )

    @extend_schema(responses=get_default_response_schema())
    @action(methods=["POST"], detail=True, url_path="sync")
    @record_operation("sync_data", "platform")
    def sync_platform(self, request, *args, **kwargs):
        """同步平台数据"""
        platform = self.get_object()

        try:
            # 异步执行同步任务
            result = sync_all_platform_data.delay(str(platform.id))

            return ApiResponse(
                data={
                    "task_id": result.id,
                    "platform_id": str(platform.id),
                    "platform_name": platform.name,
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

    @extend_schema(
        request=PlatformCredentialSerializer,
        responses=get_default_response_schema(),
    )
    @action(methods=["GET", "POST", "PUT"], detail=True, url_path="credential")
    def manage_credential(self, request, *args, **kwargs):
        """管理平台凭据"""
        platform = self.get_object()

        if request.method == "GET":
            # 获取凭据
            try:
                credential = platform.credential
                serializer = PlatformCredentialSerializer(credential)
                return ApiResponse(data=serializer.data, msg=_("Get credential success"))
            except PlatformCredential.DoesNotExist:
                return ApiResponse(
                    code=1001,
                    msg=_("Credential not found"),
                    data={"has_credential": False},
                )

        elif request.method == "POST":
            # 创建凭据
            if hasattr(platform, "credential"):
                return ApiResponse(
                    code=1001,
                    msg=_("Credential already exists, use PUT to update"),
                )

            serializer = PlatformCredentialSerializer(data={**request.data, "platform": platform.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return ApiResponse(data=serializer.data, msg=_("Credential created"))

        elif request.method == "PUT":
            # 更新凭据
            try:
                credential = platform.credential
                serializer = PlatformCredentialSerializer(credential, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return ApiResponse(data=serializer.data, msg=_("Credential updated"))
            except PlatformCredential.DoesNotExist:
                return ApiResponse(
                    code=1001,
                    msg=_("Credential not found, use POST to create"),
                )
