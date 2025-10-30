#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟机相关序列化器
"""

from rest_framework import serializers

from apps.common.core.serializers import BaseModelSerializer
from apps.virt_center.models import VirtualMachine, VMDisk, VMNetwork, VMSnapshot


class VMDiskSerializer(BaseModelSerializer):
    """虚拟机磁盘序列化器"""

    disk_type_display = serializers.CharField(source="get_disk_type_display", read_only=True)
    disk_mode_display = serializers.CharField(source="get_disk_mode_display", read_only=True)
    usage_percent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VMDisk
        fields = [
            "pk",
            "label",
            "device_key",
            "unit_number",
            "datastore_name",
            "file_path",
            "capacity_gb",
            "used_gb",
            "usage_percent",
            "disk_type",
            "disk_type_display",
            "disk_mode",
            "disk_mode_display",
            "controller_key",
            "controller_type",
            "shares",
            "extra_config",
        ]
        read_only_fields = ["pk"]

    def get_usage_percent(self, obj):
        """计算磁盘使用率"""
        if obj.capacity_gb > 0:
            return round(obj.used_gb / obj.capacity_gb * 100, 2)
        return 0


class VMNetworkSerializer(BaseModelSerializer):
    """虚拟机网络序列化器"""

    network_type_display = serializers.CharField(source="get_network_type_display", read_only=True)
    adapter_type_display = serializers.CharField(source="get_adapter_type_display", read_only=True)

    class Meta:
        model = VMNetwork
        fields = [
            "pk",
            "label",
            "device_key",
            "network_name",
            "network_type",
            "network_type_display",
            "adapter_type",
            "adapter_type_display",
            "mac_address",
            "mac_type",
            "ip_address",
            "netmask",
            "gateway",
            "connected",
            "start_connected",
            "extra_config",
        ]
        read_only_fields = ["pk"]


class VMSnapshotSerializer(BaseModelSerializer):
    """虚拟机快照序列化器"""

    class Meta:
        model = VMSnapshot
        fields = [
            "pk",
            "name",
            "snapshot_id",
            "parent",
            "description",
            "is_current",
            "is_quiesced",
            "is_memory",
            "size_mb",
            "power_state_on_snapshot",
            "snapshot_time",
            "created_time",
            "updated_time",
        ]
        read_only_fields = ["pk", "created_time", "updated_time"]


class VirtualMachineListSerializer(BaseModelSerializer):
    """虚拟机列表序列化器（简化）"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    power_state_display = serializers.CharField(source="get_power_state_display", read_only=True)
    os_type_display = serializers.CharField(source="get_os_type_display", read_only=True)
    platform_name = serializers.CharField(source="platform.name", read_only=True)
    host_name = serializers.CharField(source="host.name", read_only=True, allow_null=True)

    class Meta:
        model = VirtualMachine
        fields = [
            "pk",
            "name",
            "display_name",
            "platform",
            "platform_name",
            "host",
            "host_name",
            "status",
            "status_display",
            "power_state",
            "power_state_display",
            "os_type",
            "os_type_display",
            "os_full_name",
            "cpu_count",
            "memory_mb",
            "total_disk_gb",
            "ip_address",
            "cpu_usage_percent",
            "memory_usage_percent",
            "is_template",
            "is_active",
            "tags",
            "created_time",
            "updated_time",
        ]
        table_fields = [
            "pk",
            "name",
            "platform_name",
            "host_name",
            "status_display",
            "power_state_display",
            "os_type_display",
            "cpu_count",
            "memory_mb",
            "ip_address",
            "cpu_usage_percent",
            "memory_usage_percent",
            "is_active",
        ]
        read_only_fields = [
            "pk",
            "status",
            "cpu_usage_percent",
            "memory_usage_percent",
            "created_time",
            "updated_time",
        ]
        extra_kwargs = {
            "platform": {"required": True, "attrs": ["pk", "name"], "format": "{name}"},
            "host": {"required": False, "attrs": ["pk", "name", "ip_address"], "format": "{name}"},
        }


class VirtualMachineDetailSerializer(BaseModelSerializer):
    """虚拟机详情序列化器"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    power_state_display = serializers.CharField(source="get_power_state_display", read_only=True)
    os_type_display = serializers.CharField(source="get_os_type_display", read_only=True)
    platform_name = serializers.CharField(source="platform.name", read_only=True)
    host_name = serializers.CharField(source="host.name", read_only=True, allow_null=True)
    cluster_name = serializers.CharField(read_only=True)
    datacenter_name = serializers.CharField(read_only=True)

    # 关联数据
    disks = VMDiskSerializer(many=True, read_only=True)
    networks = VMNetworkSerializer(many=True, read_only=True)
    snapshots = VMSnapshotSerializer(many=True, read_only=True)

    # 计算字段
    memory_used_mb = serializers.IntegerField(read_only=True)

    class Meta:
        model = VirtualMachine
        fields = [
            "pk",
            "name",
            "display_name",
            "platform",
            "platform_name",
            "host",
            "host_name",
            # vSphere 标识
            "mo_ref",
            "uuid",
            "instance_uuid",
            # 位置信息
            "cluster_name",
            "datacenter_name",
            "resource_pool",
            "folder",
            # 状态信息
            "status",
            "status_display",
            "power_state",
            "power_state_display",
            "connection_state",
            # 操作系统信息
            "os_type",
            "os_type_display",
            "os_full_name",
            "guest_id",
            "guest_state",
            "tools_status",
            "tools_version",
            # 硬件配置
            "cpu_count",
            "cpu_cores_per_socket",
            "memory_mb",
            "memory_used_mb",
            "hardware_version",
            # 网络信息
            "ip_address",
            "mac_address",
            "hostname",
            # 磁盘信息
            "disk_count",
            "total_disk_gb",
            # 资源使用
            "cpu_usage_percent",
            "memory_usage_percent",
            # 快照信息
            "has_snapshots",
            "snapshot_count",
            # 管理信息
            "is_template",
            "is_active",
            "auto_start",
            "tags",
            "notes",
            "extra_info",
            # 时间信息
            "boot_time",
            "last_seen",
            "created_time",
            "updated_time",
            # 关联数据
            "disks",
            "networks",
            "snapshots",
        ]
        read_only_fields = [
            "pk",
            "mo_ref",
            "uuid",
            "instance_uuid",
            "status",
            "power_state",
            "connection_state",
            "guest_id",
            "guest_state",
            "tools_status",
            "tools_version",
            "hardware_version",
            "disk_count",
            "total_disk_gb",
            "cpu_usage_percent",
            "memory_usage_percent",
            "has_snapshots",
            "snapshot_count",
            "boot_time",
            "last_seen",
            "created_time",
            "updated_time",
        ]
        extra_kwargs = {
            "platform": {"required": True, "attrs": ["pk", "name"], "format": "{name}"},
            "host": {"required": False, "attrs": ["pk", "name", "ip_address"], "format": "{name}"},
        }


class VirtualMachineSerializer(BaseModelSerializer):
    """虚拟机序列化器（用于创建/更新）"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    power_state_display = serializers.CharField(source="get_power_state_display", read_only=True)
    os_type_display = serializers.CharField(source="get_os_type_display", read_only=True)

    class Meta:
        model = VirtualMachine
        fields = [
            "pk",
            "name",
            "display_name",
            "platform",
            "host",
            "status",
            "status_display",
            "power_state",
            "power_state_display",
            "os_type",
            "os_type_display",
            "os_full_name",
            "cpu_count",
            "memory_mb",
            "is_template",
            "is_active",
            "auto_start",
            "tags",
            "notes",
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
            "host": {"required": False, "attrs": ["pk", "name", "ip_address"], "format": "{name}"},
        }


class VMOperationSerializer(serializers.Serializer):
    """虚拟机操作序列化器"""

    operation = serializers.ChoiceField(
        required=True,
        choices=[
            ("power_on", "开机"),
            ("power_off", "关机"),
            ("suspend", "挂起"),
            ("reset", "重启"),
            ("shutdown", "关闭客户机"),
            ("reboot", "重启客户机"),
        ],
        help_text="操作类型",
    )
    force = serializers.BooleanField(required=False, default=False, help_text="是否强制执行")
