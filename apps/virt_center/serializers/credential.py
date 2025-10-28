#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
平台凭据序列化器
"""

from rest_framework import serializers

from apps.virt_center.models import Platform, PlatformCredential


class PlatformCredentialSerializer(serializers.ModelSerializer):
    """平台凭据序列化器"""

    auth_type_display = serializers.CharField(source="get_auth_type_display", read_only=True)
    platform_name = serializers.CharField(source="platform.name", read_only=True)

    class Meta:
        model = PlatformCredential
        fields = [
            "id",
            "platform",
            "platform_name",
            "auth_type",
            "auth_type_display",
            "username",
            "password",
            "token",
            "session_id",
            "session_expires",
            "extra_data",
            "created_time",
            "updated_time",
        ]
        read_only_fields = [
            "id",
            "session_id",
            "session_expires",
            "created_time",
            "updated_time",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "token": {"write_only": True},
        }

    def validate_platform(self, value):
        """验证平台"""
        # 检查平台是否已存在凭据（创建时）
        if not self.instance and hasattr(value, "credential"):
            raise serializers.ValidationError("该平台已存在认证凭据，请使用更新接口")
        return value
