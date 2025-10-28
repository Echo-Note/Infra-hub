#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
平台相关序列化器
"""

from rest_framework import serializers

from apps.virt_center.models import Platform


class PlatformSerializer(serializers.ModelSerializer):
    """平台序列化器"""

    platform_type_display = serializers.CharField(source="get_platform_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    connection_url = serializers.CharField(read_only=True)

    class Meta:
        model = Platform
        fields = [
            "id",
            "name",
            "platform_type",
            "platform_type_display",
            "host",
            "port",
            "is_ssl",
            "ssl_verify",
            "status",
            "status_display",
            "is_active",
            "region",
            "datacenter",
            "version",
            "build",
            "total_hosts",
            "total_vms",
            "total_clusters",
            "last_sync_time",
            "connection_url",
            "tags",
            "created_time",
            "updated_time",
        ]
        read_only_fields = [
            "id",
            "status",
            "version",
            "build",
            "total_hosts",
            "total_vms",
            "total_clusters",
            "last_sync_time",
            "created_time",
            "updated_time",
        ]


class SyncTaskSerializer(serializers.Serializer):
    """同步任务序列化器"""

    platform_id = serializers.UUIDField(required=True, help_text="平台ID")
    sync_type = serializers.ChoiceField(
        required=False,
        default="all",
        choices=[
            ("all", "全部数据"),
            ("platform", "平台信息"),
            ("hosts", "主机信息"),
            ("vms", "虚拟机信息"),
            ("datastores", "存储信息"),
            ("templates", "模板信息"),
        ],
        help_text="同步类型",
    )

    def validate_platform_id(self, value):
        """验证平台ID"""
        try:
            platform = Platform.objects.get(id=value)
            if not platform.is_active:
                raise serializers.ValidationError("平台未启用")
            return value
        except Platform.DoesNotExist:
            raise serializers.ValidationError("平台不存在")
