#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
同步任务视图
"""

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.common.core.response import ApiResponse
from apps.common.swagger.utils import get_default_response_schema
from apps.virt_center.models import Platform
from apps.virt_center.serializers import SyncTaskSerializer
from apps.virt_center.tasks import (
    sync_all_platform_data,
    sync_all_platforms,
    sync_datastores,
    sync_hosts,
    sync_platform_info,
    sync_templates,
    sync_vms,
)


class SyncTaskViewSet(viewsets.ViewSet):
    """同步任务视图集"""

    @extend_schema(
        request=SyncTaskSerializer,
        responses=get_default_response_schema(),
    )
    @action(methods=["POST"], detail=False, url_path="sync-platform")
    def sync_platform(self, request):
        """同步指定平台的数据"""
        serializer = SyncTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        platform_id = str(serializer.validated_data["platform_id"])
        sync_type = serializer.validated_data.get("sync_type", "all")

        # 根据同步类型选择任务
        task_map = {
            "all": sync_all_platform_data,
            "platform": sync_platform_info,
            "hosts": sync_hosts,
            "vms": sync_vms,
            "datastores": sync_datastores,
            "templates": sync_templates,
        }

        task = task_map.get(sync_type)
        if not task:
            return ApiResponse(
                code=1001,
                msg=_("Invalid sync type"),
                data={"sync_type": sync_type},
            )

        try:
            # 异步执行同步任务
            result = task.delay(platform_id)

            platform = Platform.objects.get(id=platform_id)

            return ApiResponse(
                data={
                    "task_id": result.id,
                    "platform_id": platform_id,
                    "platform_name": platform.name,
                    "sync_type": sync_type,
                    "message": f"{sync_type} 同步任务已启动",
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
    @action(methods=["POST"], detail=False, url_path="sync-all-platforms")
    def sync_all_platforms_view(self, request):
        """同步所有启用的平台数据"""
        try:
            # 异步执行同步任务
            result = sync_all_platforms.delay()

            return ApiResponse(
                data={
                    "task_id": result.id,
                    "message": "所有平台同步任务已启动",
                },
                msg=_("Sync all platforms task started"),
            )

        except Exception as e:
            return ApiResponse(
                code=1001,
                msg=_("Failed to start sync task"),
                data={"error": str(e)},
            )

    @extend_schema(responses=get_default_response_schema())
    @action(methods=["GET"], detail=False, url_path="task-status/(?P<task_id>[^/.]+)")
    def task_status(self, request, task_id=None):
        """查询任务状态"""
        from celery.result import AsyncResult

        try:
            result = AsyncResult(task_id)

            response_data = {
                "task_id": task_id,
                "status": result.state,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
            }

            if result.ready():
                if result.successful():
                    response_data["result"] = result.result
                else:
                    response_data["error"] = str(result.info)

            return ApiResponse(data=response_data, msg=_("Task status retrieved"))

        except Exception as e:
            return ApiResponse(
                code=1001,
                msg=_("Failed to get task status"),
                data={"error": str(e)},
            )
