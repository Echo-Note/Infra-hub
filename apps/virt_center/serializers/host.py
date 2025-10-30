#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
宿主机相关序列化器
"""

from rest_framework import serializers

from apps.common.core.serializers import BaseModelSerializer
from apps.virt_center.models import Host, HostNetwork, HostResource


class HostResourceSerializer(BaseModelSerializer):
    """主机资源详情序列化器"""

    cpu_usage_percent = serializers.SerializerMethodField(read_only=True)
    memory_usage_percent = serializers.SerializerMethodField(read_only=True)
    storage_usage_percent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HostResource
        fields = [
            "pk",
            # CPU 详细使用情况
            "cpu_used_mhz",
            "cpu_total_mhz",
            "cpu_reserved_mhz",
            "cpu_usage_percent",
            # 内存详细使用情况
            "memory_used",
            "memory_free",
            "memory_active",
            "memory_consumed",
            "memory_usage_percent",
            # 存储信息
            "storage_total",
            "storage_used",
            "storage_free",
            "storage_uncommitted",
            "storage_usage_percent",
            # 网络流量统计
            "network_rx_bytes",
            "network_tx_bytes",
            "network_rx_packets",
            "network_tx_packets",
            # 性能指标
            "uptime_seconds",
            "updated_time",
        ]
        read_only_fields = ["pk", "updated_time"]

    def get_cpu_usage_percent(self, obj):
        """计算 CPU 使用率"""
        if obj.cpu_total_mhz > 0:
            return round(obj.cpu_used_mhz / obj.cpu_total_mhz * 100, 2)
        return 0

    def get_memory_usage_percent(self, obj):
        """计算内存使用率"""
        total = obj.memory_used + obj.memory_free
        if total > 0:
            return round(obj.memory_used / total * 100, 2)
        return 0

    def get_storage_usage_percent(self, obj):
        """计算存储使用率"""
        if obj.storage_total > 0:
            return round(obj.storage_used / obj.storage_total * 100, 2)
        return 0


class HostNetworkSerializer(BaseModelSerializer):
    """主机网络序列化器"""

    network_type_display = serializers.CharField(source="get_network_type_display", read_only=True)

    class Meta:
        model = HostNetwork
        fields = [
            "pk",
            "name",
            "network_type",
            "network_type_display",
            "vswitch_name",
            "portgroup_name",
            "physical_nics",
            "vlan_id",
            "ip_address",
            "netmask",
            "gateway",
            "mtu",
            "speed_mbps",
            "vmotion_enabled",
            "management_enabled",
            "vsan_enabled",
            "ft_enabled",
            "is_active",
            "extra_config",
        ]
        read_only_fields = ["pk"]


class HostListSerializer(BaseModelSerializer):
    """主机列表序列化器（简化）"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    power_state_display = serializers.CharField(source="get_power_state_display", read_only=True)
    platform_name = serializers.CharField(source="platform.name", read_only=True)
    memory_used_mb = serializers.IntegerField(read_only=True)
    memory_available_mb = serializers.IntegerField(read_only=True)

    class Meta:
        model = Host
        fields = [
            "id",
            "name",
            "hostname",
            "ip_address",
            "platform",
            "platform_name",
            "cluster_name",
            "datacenter_name",
            "status",
            "status_display",
            "power_state",
            "power_state_display",
            "vendor",
            "model",
            "esxi_version",
            "cpu_cores",
            "cpu_threads",
            "memory_total",
            "memory_used_mb",
            "memory_available_mb",
            "vm_count",
            "cpu_usage",
            "memory_usage",
            "is_active",
            "in_maintenance",
            "tags",
            "created_time",
            "updated_time",
        ]
        table_fields = [
            "pk",
            "name",
            "ip_address",
            "platform_name",
            "cluster_name",
            "status_display",
            "power_state_display",
            "cpu_cores",
            "memory_total",
            "vm_count",
            "cpu_usage",
            "memory_usage",
            "is_active",
        ]
        read_only_fields = [
            "pk",
            "status",
            "power_state",
            "vm_count",
            "cpu_usage",
            "memory_usage",
            "created_time",
            "updated_time",
        ]
        extra_kwargs = {
            "platform": {"required": True, "attrs": ["pk", "name"], "format": "{name}"},
        }


class HostDetailSerializer(BaseModelSerializer):
    """主机详情序列化器"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    power_state_display = serializers.CharField(source="get_power_state_display", read_only=True)
    platform_name = serializers.CharField(source="platform.name", read_only=True)
    memory_used_mb = serializers.IntegerField(read_only=True)
    memory_available_mb = serializers.IntegerField(read_only=True)

    # 关联数据
    resource = HostResourceSerializer(read_only=True)
    networks = HostNetworkSerializer(many=True, read_only=True)

    # 虚拟机列表（简化）
    vms = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Host
        fields = [
            "id",
            "name",
            "hostname",
            "ip_address",
            "platform",
            "platform_name",
            # vSphere 对象标识
            "mo_ref",
            "uuid",
            # 集群信息
            "cluster_name",
            "datacenter_name",
            # 状态信息
            "status",
            "status_display",
            "power_state",
            "power_state_display",
            "connection_state",
            # 系统信息
            "vendor",
            "model",
            "esxi_version",
            "esxi_build",
            # CPU 信息
            "cpu_model",
            "cpu_cores",
            "cpu_threads",
            "cpu_sockets",
            "cpu_frequency",
            # 内存信息
            "memory_total",
            "memory_used_mb",
            "memory_available_mb",
            # 资源使用统计
            "vm_count",
            "cpu_usage",
            "memory_usage",
            # 管理信息
            "is_active",
            "in_maintenance",
            "tags",
            "extra_info",
            "last_seen",
            "created_time",
            "updated_time",
            # 关联数据
            "resource",
            "networks",
            "vms",
        ]
        read_only_fields = [
            "pk",
            "mo_ref",
            "uuid",
            "status",
            "power_state",
            "connection_state",
            "vm_count",
            "cpu_usage",
            "memory_usage",
            "last_seen",
            "created_time",
            "updated_time",
        ]
        extra_kwargs = {
            "platform": {"required": True, "attrs": ["pk", "name"], "format": "{name}"},
        }

    def get_vms(self, obj):
        """获取主机上的虚拟机列表（简化）"""
        from apps.virt_center.models import VirtualMachine

        vms = VirtualMachine.objects.filter(host=obj, is_active=True).values(
            "id", "name", "power_state", "cpu_count", "memory_mb", "os_type"
        )[
            :10
        ]  # 最多返回 10 个
        return list(vms)


class HostSerializer(BaseModelSerializer):
    """主机序列化器（用于创建/更新）"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    power_state_display = serializers.CharField(source="get_power_state_display", read_only=True)

    class Meta:
        model = Host
        fields = [
            "id",
            "name",
            "hostname",
            "ip_address",
            "platform",
            "cluster_name",
            "datacenter_name",
            "status",
            "status_display",
            "power_state",
            "power_state_display",
            "is_active",
            "in_maintenance",
            "tags",
            "extra_info",
            "created_time",
            "updated_time",
        ]
        read_only_fields = [
            "pk",
            "status",
            "power_state",
            "created_time",
            "updated_time",
        ]
        extra_kwargs = {
            "platform": {"required": True, "attrs": ["pk", "name"], "format": "{name}"},
        }


class HostOperationSerializer(serializers.Serializer):
    """主机操作序列化器"""

    operation = serializers.ChoiceField(
        required=True,
        choices=[
            ("enter_maintenance", "进入维护模式"),
            ("exit_maintenance", "退出维护模式"),
            ("reboot", "重启主机"),
            ("shutdown", "关闭主机"),
        ],
        help_text="操作类型",
    )
    force = serializers.BooleanField(required=False, default=False, help_text="是否强制执行")
