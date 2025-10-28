#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
ESXi 宿主机模型
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.core.models import DbAuditModel, DbUuidModel

from .platform import Platform


class Host(DbUuidModel, DbAuditModel):
    """ESXi 宿主机"""

    class Status(models.IntegerChoices):
        """主机状态"""

        OFFLINE = 0, "离线"
        ONLINE = 1, "在线"
        MAINTENANCE = 2, "维护中"
        ERROR = 3, "异常"
        STANDBY = 4, "待机"
        UNKNOWN = 5, "未知"

    class PowerState(models.TextChoices):
        """电源状态"""

        POWERED_ON = "poweredOn", "已开机"
        POWERED_OFF = "poweredOff", "已关机"
        STANDBY = "standBy", "待机"
        UNKNOWN = "unknown", "未知"

    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name="hosts",
        verbose_name="所属平台",
        help_text="所属的 vCenter 平台",
    )
    name = models.CharField(max_length=128, verbose_name="主机名称", help_text="ESXi 主机名称", db_index=True)
    hostname = models.CharField(
        max_length=256, verbose_name="主机域名", blank=True, null=True, help_text="完整域名 FQDN"
    )
    ip_address = models.GenericIPAddressField(verbose_name="IP 地址", help_text="ESXi 管理 IP 地址", db_index=True)

    # vSphere 对象标识
    mo_ref = models.CharField(
        max_length=128, verbose_name="MO 引用", blank=True, null=True, help_text="vSphere Managed Object Reference ID"
    )
    uuid = models.CharField(
        max_length=128,
        verbose_name="硬件 UUID",
        blank=True,
        null=True,
        unique=True,
        help_text="ESXi 主机硬件 UUID",
    )

    # 集群信息
    cluster_name = models.CharField(
        max_length=128, verbose_name="集群名称", blank=True, null=True, help_text="所属 vSphere 集群"
    )
    datacenter_name = models.CharField(
        max_length=128, verbose_name="数据中心", blank=True, null=True, help_text="所属 vSphere 数据中心"
    )

    # 状态信息
    status = models.SmallIntegerField(
        choices=Status.choices, default=Status.OFFLINE, verbose_name="运行状态", help_text="主机运行状态"
    )
    power_state = models.CharField(
        max_length=32,
        choices=PowerState.choices,
        default=PowerState.UNKNOWN,
        verbose_name="电源状态",
        help_text="主机电源状态",
    )
    connection_state = models.CharField(
        max_length=64, verbose_name="连接状态", blank=True, null=True, help_text="vCenter 连接状态"
    )

    # 系统信息
    vendor = models.CharField(
        max_length=128, verbose_name="硬件厂商", blank=True, null=True, help_text="服务器硬件厂商"
    )
    model = models.CharField(max_length=128, verbose_name="服务器型号", blank=True, null=True, help_text="服务器型号")
    esxi_version = models.CharField(
        max_length=64, verbose_name="ESXi 版本", blank=True, null=True, help_text="ESXi 版本号"
    )
    esxi_build = models.CharField(
        max_length=64, verbose_name="ESXi 构建号", blank=True, null=True, help_text="ESXi 构建号"
    )

    # CPU 信息
    cpu_model = models.CharField(max_length=256, verbose_name="CPU 型号", blank=True, null=True, help_text="处理器型号")
    cpu_cores = models.IntegerField(verbose_name="CPU 核心数", default=0, help_text="物理 CPU 核心总数")
    cpu_threads = models.IntegerField(verbose_name="CPU 线程数", default=0, help_text="逻辑 CPU 线程总数")
    cpu_sockets = models.IntegerField(verbose_name="CPU 插槽数", default=0, help_text="物理 CPU 插槽数量")
    cpu_frequency = models.IntegerField(verbose_name="CPU 频率", default=0, help_text="CPU 频率，单位 MHz")

    # 内存信息
    memory_total = models.BigIntegerField(verbose_name="总内存", default=0, help_text="总内存大小，单位 MB")

    # 资源使用统计
    vm_count = models.IntegerField(verbose_name="虚拟机数量", default=0, help_text="该主机上运行的虚拟机数量")
    cpu_usage = models.FloatField(
        verbose_name="CPU 使用率",
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="CPU 使用率百分比",
    )
    memory_usage = models.FloatField(
        verbose_name="内存使用率",
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="内存使用率百分比",
    )

    # 管理信息
    is_active = models.BooleanField(verbose_name="启用状态", default=True, help_text="是否启用管理", db_index=True)
    in_maintenance = models.BooleanField(verbose_name="维护模式", default=False, help_text="是否处于维护模式")
    tags = models.JSONField(verbose_name="标签", default=list, blank=True, help_text="自定义标签列表")
    extra_info = models.JSONField(verbose_name="扩展信息", default=dict, blank=True, help_text="其他扩展信息")
    last_seen = models.DateTimeField(verbose_name="最后在线", null=True, blank=True, help_text="最后一次在线时间")

    class Meta:
        db_table = "virt_host"
        verbose_name = "ESXi 主机"
        verbose_name_plural = verbose_name
        ordering = ["-created_time"]
        unique_together = [["platform", "name"]]
        indexes = [
            models.Index(fields=["platform", "status"]),
            models.Index(fields=["platform", "is_active"]),
            models.Index(fields=["cluster_name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    @property
    def memory_used_mb(self):
        """已使用内存（MB）"""
        return int(self.memory_total * self.memory_usage / 100)

    @property
    def memory_available_mb(self):
        """可用内存（MB）"""
        return self.memory_total - self.memory_used_mb


class HostResource(DbUuidModel):
    """主机资源详细信息"""

    host = models.OneToOneField(Host, on_delete=models.CASCADE, related_name="resource", verbose_name="所属主机")

    # CPU 详细使用情况
    cpu_used_mhz = models.IntegerField(verbose_name="CPU 已用", default=0, help_text="已使用的 CPU 频率，单位 MHz")
    cpu_total_mhz = models.IntegerField(verbose_name="CPU 总量", default=0, help_text="总 CPU 频率，单位 MHz")
    cpu_reserved_mhz = models.IntegerField(verbose_name="CPU 预留", default=0, help_text="预留的 CPU 频率，单位 MHz")

    # 内存详细使用情况
    memory_used = models.BigIntegerField(verbose_name="已用内存", default=0, help_text="已使用内存，单位 MB")
    memory_free = models.BigIntegerField(verbose_name="空闲内存", default=0, help_text="空闲内存，单位 MB")
    memory_active = models.BigIntegerField(verbose_name="活动内存", default=0, help_text="活动内存，单位 MB")
    memory_consumed = models.BigIntegerField(verbose_name="消耗内存", default=0, help_text="虚拟机消耗内存，单位 MB")

    # 存储信息
    storage_total = models.BigIntegerField(verbose_name="总存储", default=0, help_text="总存储容量，单位 GB")
    storage_used = models.BigIntegerField(verbose_name="已用存储", default=0, help_text="已使用存储，单位 GB")
    storage_free = models.BigIntegerField(verbose_name="空闲存储", default=0, help_text="空闲存储，单位 GB")
    storage_uncommitted = models.BigIntegerField(
        verbose_name="未提交存储", default=0, help_text="未提交的存储空间，单位 GB"
    )

    # 网络流量统计
    network_rx_bytes = models.BigIntegerField(verbose_name="网络接收", default=0, help_text="网络接收字节数")
    network_tx_bytes = models.BigIntegerField(verbose_name="网络发送", default=0, help_text="网络发送字节数")
    network_rx_packets = models.BigIntegerField(verbose_name="接收包数", default=0, help_text="网络接收包数")
    network_tx_packets = models.BigIntegerField(verbose_name="发送包数", default=0, help_text="网络发送包数")

    # 性能指标
    uptime_seconds = models.BigIntegerField(verbose_name="运行时长", default=0, help_text="运行时长，单位秒")

    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间", help_text="资源信息最后更新时间")

    class Meta:
        db_table = "virt_host_resource"
        verbose_name = "主机资源详情"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.host.name} - 资源详情"


class HostNetwork(DbUuidModel):
    """主机网络配置"""

    class NetworkType(models.TextChoices):
        """网络类型"""

        VSWITCH = "vswitch", "标准交换机"
        DVSWITCH = "dvswitch", "分布式交换机"
        PORTGROUP = "portgroup", "端口组"
        VMKERNEL = "vmkernel", "VMkernel"

    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="networks", verbose_name="所属主机")
    name = models.CharField(max_length=128, verbose_name="网络名称", help_text="vSwitch 或端口组名称")
    network_type = models.CharField(
        max_length=32, choices=NetworkType.choices, verbose_name="网络类型", help_text="虚拟交换机类型"
    )

    # vSwitch 信息
    vswitch_name = models.CharField(
        max_length=128, verbose_name="虚拟交换机", blank=True, null=True, help_text="所属虚拟交换机名称"
    )
    portgroup_name = models.CharField(
        max_length=128, verbose_name="端口组", blank=True, null=True, help_text="端口组名称"
    )

    # 物理网卡信息
    physical_nics = models.JSONField(verbose_name="物理网卡", default=list, blank=True, help_text="绑定的物理网卡列表")

    # VLAN 配置
    vlan_id = models.IntegerField(verbose_name="VLAN ID", null=True, blank=True, help_text="VLAN ID，0 表示无 VLAN")

    # IP 配置（针对 VMkernel）
    ip_address = models.GenericIPAddressField(
        verbose_name="IP 地址", null=True, blank=True, help_text="VMkernel IP 地址"
    )
    netmask = models.CharField(max_length=64, verbose_name="子网掩码", blank=True, null=True, help_text="子网掩码")
    gateway = models.GenericIPAddressField(verbose_name="网关", null=True, blank=True, help_text="默认网关")

    # 网卡性能
    mtu = models.IntegerField(verbose_name="MTU", default=1500, help_text="最大传输单元")
    speed_mbps = models.IntegerField(verbose_name="带宽", default=1000, help_text="网络带宽，单位 Mbps")

    # 启用的功能
    vmotion_enabled = models.BooleanField(verbose_name="启用 vMotion", default=False, help_text="是否启用 vMotion")
    management_enabled = models.BooleanField(verbose_name="启用管理", default=False, help_text="是否启用管理流量")
    vsan_enabled = models.BooleanField(verbose_name="启用 vSAN", default=False, help_text="是否启用 vSAN")
    ft_enabled = models.BooleanField(verbose_name="启用容错", default=False, help_text="是否启用容错功能")

    is_active = models.BooleanField(verbose_name="启用状态", default=True, help_text="网络是否启用")
    extra_config = models.JSONField(verbose_name="扩展配置", default=dict, blank=True, help_text="其他网络配置信息")

    class Meta:
        db_table = "virt_host_network"
        verbose_name = "主机网络"
        verbose_name_plural = verbose_name
        unique_together = [["host", "name"]]
        indexes = [
            models.Index(fields=["host", "network_type"]),
        ]

    def __str__(self):
        return f"{self.host.name} - {self.name}"
