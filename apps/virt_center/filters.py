#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心过滤器
"""

from django_filters import rest_framework as filters

from apps.common.core.filter import BaseFilterSet
from apps.virt_center.models import Platform, PlatformCredential


class PlatformFilter(BaseFilterSet):
    """平台过滤器"""

    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    host = filters.CharFilter(field_name="host", lookup_expr="icontains")
    region = filters.CharFilter(field_name="region", lookup_expr="icontains")
    datacenter = filters.CharFilter(field_name="datacenter", lookup_expr="icontains")

    class Meta:
        model = Platform
        fields = [
            "name",
            "host",
            "platform_type",
            "status",
            "is_active",
            "region",
            "datacenter",
        ]


class PlatformCredentialFilter(BaseFilterSet):
    """平台凭据过滤器"""

    class Meta:
        model = PlatformCredential
        fields = ["platform", "auth_type"]
