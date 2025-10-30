#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心过滤器
"""

from django_filters import rest_framework as filters

from apps.common.core.filter import BaseFilterSet
from apps.virt_center.models import Host, Platform, PlatformCredential, VirtualMachine


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


class HostFilter(BaseFilterSet):
    """主机过滤器"""

    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    hostname = filters.CharFilter(field_name="hostname", lookup_expr="icontains")
    ip_address = filters.CharFilter(field_name="ip_address", lookup_expr="icontains")
    cluster_name = filters.CharFilter(field_name="cluster_name", lookup_expr="icontains")
    datacenter_name = filters.CharFilter(field_name="datacenter_name", lookup_expr="icontains")

    class Meta:
        model = Host
        fields = [
            "name",
            "hostname",
            "ip_address",
            "platform",
            "cluster_name",
            "datacenter_name",
            "status",
            "power_state",
            "is_active",
            "in_maintenance",
        ]


class VirtualMachineFilter(BaseFilterSet):
    """虚拟机过滤器"""

    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    hostname = filters.CharFilter(field_name="hostname", lookup_expr="icontains")
    ip_address = filters.CharFilter(field_name="ip_address", lookup_expr="icontains")
    cluster_name = filters.CharFilter(field_name="cluster_name", lookup_expr="icontains")
    datacenter_name = filters.CharFilter(field_name="datacenter_name", lookup_expr="icontains")

    class Meta:
        model = VirtualMachine
        fields = [
            "name",
            "hostname",
            "ip_address",
            "platform",
            "host",
            "cluster_name",
            "datacenter_name",
            "status",
            "power_state",
            "os_type",
            "is_template",
            "is_active",
        ]
