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
from apps.virt_center.models import Platform
from apps.virt_center.serializers import PlatformSerializer
from apps.virt_center.tasks import sync_all_platform_data


class PlatformViewSet(BaseModelSet):
    """平台管理视图集"""

    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    ordering_fields = ["created_time", "updated_time", "name"]
    search_fields = ["name", "host", "region", "datacenter"]
    filterset_fields = {
        "platform_type": ["exact"],
        "status": ["exact"],
        "is_active": ["exact"],
        "region": ["exact", "icontains"],
    }

    @extend_schema(responses=get_default_response_schema())
    @action(methods=["POST"], detail=True, url_path="test-connection")
    def test_connection(self, request, *args, **kwargs):
        """测试平台连接"""
        platform = self.get_object()

        try:
            from apps.virt_center.utils.vsphere_client import get_vsphere_client

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

            return ApiResponse(
                code=1001,
                msg=_("Platform connection failed"),
                data={"connected": False, "error": str(e)},
            )

    @extend_schema(responses=get_default_response_schema())
    @action(methods=["POST"], detail=True, url_path="sync")
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
