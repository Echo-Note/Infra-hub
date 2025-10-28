#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟机模型
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.core.models import DbAuditModel, DbUuidModel

from .host import Host
from .platform import Platform


class VirtualMachine(DbUuidModel, DbAuditModel):
    """虚拟机"""

    class Status(models.IntegerChoices):
        """虚拟机状态"""

        UNKNOWN = 0, "未知"
        RUNNING = 1, "运行中"
        STOPPED = 2, "已停止"
        SUSPENDED = 3, "已挂起"
        CREATING = 4, "创建中"
        DELETING = 5, "删除中"
        ERROR = 6, "异常"

    class PowerState(models.TextChoices):
        """电源状态"""

        POWERED_ON = "poweredOn", "已开机"
        POWERED_OFF = "poweredOff", "已关机"
        SUSPENDED = "suspended", "已挂起"

    class OSType(models.TextChoices):
        """操作系统类型"""

        WINDOWS = "windows", "Windows"
        LINUX = "linux", "Linux"
        CENTOS = "centos", "CentOS"
        UBUNTU = "ubuntu", "Ubuntu"
        DEBIAN = "debian", "Debian"
        REDHAT = "redhat", "Red Hat"
        OTHER = "other", "其他"

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="vms", verbose_name="所属平台", help_text="所属 vCenter 平台"
    )
    host = models.ForeignKey(
        Host,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vms",
        verbose_name="所在主机",
        help_text="当前运行的 ESXi 主机",
    )

    # 基本信息
    name = models.CharField(max_length=128, verbose_name="虚拟机名称", help_text="虚拟机显示名称", db_index=True)
    display_name = models.CharField(
        max_length=256, verbose_name="显示名称", blank=True, null=True, help_text="虚拟机显示名称"
    )

    # vSphere 对象标识
    mo_ref = models.CharField(
        max_length=128, verbose_name="MO 引用", blank=True, null=True, help_text="vSphere Managed Object Reference ID"
    )
    uuid = models.CharField(
        max_length=128, verbose_name="UUID", blank=True, null=True, unique=True, help_text="虚拟机 UUID"
    )
    instance_uuid = models.CharField(
        max_length=128, verbose_name="实例 UUID", blank=True, null=True, help_text="vCenter 实例 UUID"
    )

    # 位置信息
    cluster_name = models.CharField(
        max_length=128, verbose_name="集群名称", blank=True, null=True, help_text="所属 vSphere 集群"
    )
    datacenter_name = models.CharField(
        max_length=128, verbose_name="数据中心", blank=True, null=True, help_text="所属数据中心"
    )
    resource_pool = models.CharField(
        max_length=256, verbose_name="资源池", blank=True, null=True, help_text="所属资源池路径"
    )
    folder = models.CharField(
        max_length=512, verbose_name="文件夹", blank=True, null=True, help_text="虚拟机所在文件夹路径"
    )

    # 状态信息
    status = models.SmallIntegerField(
        choices=Status.choices, default=Status.UNKNOWN, verbose_name="运行状态", help_text="虚拟机运行状态"
    )
    power_state = models.CharField(
        max_length=32,
        choices=PowerState.choices,
        default=PowerState.POWERED_OFF,
        verbose_name="电源状态",
        help_text="虚拟机电源状态",
    )
    connection_state = models.CharField(
        max_length=64, verbose_name="连接状态", blank=True, null=True, help_text="与主机的连接状态"
    )

    # 操作系统信息
    os_type = models.CharField(
        max_length=64,
        choices=OSType.choices,
        default=OSType.OTHER,
        verbose_name="操作系统类型",
        help_text="操作系统类型",
    )
    os_full_name = models.CharField(
        max_length=256, verbose_name="操作系统", blank=True, null=True, help_text="完整的操作系统名称"
    )
    guest_id = models.CharField(
        max_length=128, verbose_name="客户机 ID", blank=True, null=True, help_text="vSphere Guest ID"
    )
    guest_state = models.CharField(
        max_length=64, verbose_name="客户机状态", blank=True, null=True, help_text="VMware Tools 状态"
    )
    tools_status = models.CharField(
        max_length=64, verbose_name="Tools 状态", blank=True, null=True, help_text="VMware Tools 运行状态"
    )
    tools_version = models.CharField(
        max_length=64, verbose_name="Tools 版本", blank=True, null=True, help_text="VMware Tools 版本"
    )

    # 硬件配置
    cpu_count = models.IntegerField(verbose_name="CPU 数量", default=1, help_text="分配的 vCPU 数量")
    cpu_cores_per_socket = models.IntegerField(
        verbose_name="每插槽核心数", default=1, help_text="每个 CPU 插槽的核心数"
    )
    memory_mb = models.IntegerField(verbose_name="内存大小", default=1024, help_text="分配的内存大小，单位 MB")

    # 虚拟硬件版本
    hardware_version = models.CharField(
        max_length=32, verbose_name="虚拟硬件版本", blank=True, null=True, help_text="虚拟机硬件版本"
    )

    # 网络信息
    ip_address = models.GenericIPAddressField(
        verbose_name="IP 地址", null=True, blank=True, help_text="虚拟机主 IP 地址"
    )
    mac_address = models.CharField(
        max_length=64, verbose_name="MAC 地址", blank=True, null=True, help_text="主网卡 MAC 地址"
    )
    hostname = models.CharField(max_length=256, verbose_name="主机名", blank=True, null=True, help_text="虚拟机主机名")

    # 磁盘信息摘要
    disk_count = models.IntegerField(verbose_name="磁盘数量", default=0, help_text="虚拟磁盘数量")
    total_disk_gb = models.IntegerField(verbose_name="磁盘总量", default=0, help_text="磁盘总容量，单位 GB")

    # 资源使用（快照值，详细监控数据在 VMMetrics 中）
    cpu_usage_percent = models.FloatField(
        verbose_name="CPU 使用率",
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="CPU 使用率百分比（快照）",
    )
    memory_usage_percent = models.FloatField(
        verbose_name="内存使用率",
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="内存使用率百分比（快照）",
    )

    # 快照信息
    has_snapshots = models.BooleanField(verbose_name="存在快照", default=False, help_text="是否存在快照")
    snapshot_count = models.IntegerField(verbose_name="快照数量", default=0, help_text="快照数量")

    # 管理信息
    is_template = models.BooleanField(
        verbose_name="是否模板", default=False, help_text="是否为虚拟机模板", db_index=True
    )
    is_active = models.BooleanField(verbose_name="启用状态", default=True, help_text="是否启用管理", db_index=True)
    auto_start = models.BooleanField(verbose_name="自动启动", default=False, help_text="主机启动时是否自动启动虚拟机")

    # 标签和备注
    tags = models.JSONField(verbose_name="标签", default=list, blank=True, help_text="自定义标签列表")
    notes = models.TextField(verbose_name="备注", blank=True, null=True, help_text="虚拟机备注信息")
    extra_info = models.JSONField(verbose_name="扩展信息", default=dict, blank=True, help_text="其他扩展信息")

    # 时间信息
    boot_time = models.DateTimeField(verbose_name="启动时间", null=True, blank=True, help_text="虚拟机启动时间")
    last_seen = models.DateTimeField(verbose_name="最后在线", null=True, blank=True, help_text="最后一次在线时间")

    class Meta:
        db_table = "virt_vm"
        verbose_name = "虚拟机"
        verbose_name_plural = verbose_name
        ordering = ["-created_time"]
        unique_together = [["platform", "name"]]
        indexes = [
            models.Index(fields=["platform", "status"]),
            models.Index(fields=["platform", "is_active"]),
            models.Index(fields=["host", "power_state"]),
            models.Index(fields=["is_template"]),
        ]

    def __str__(self):
        return f"{self.name}"

    @property
    def memory_used_mb(self):
        """已使用内存（MB）"""
        return int(self.memory_mb * self.memory_usage_percent / 100)


class VMDisk(DbUuidModel):
    """虚拟机磁盘"""

    class DiskType(models.TextChoices):
        """磁盘类型"""

        THIN = "thin", "精简置备"
        THICK_LAZY = "thick_lazy", "厚置备延迟置零"
        THICK_EAGER = "thick_eager", "厚置备置零"

    class DiskMode(models.TextChoices):
        """磁盘模式"""

        PERSISTENT = "persistent", "持久"
        INDEPENDENT_PERSISTENT = "independent_persistent", "独立持久"
        INDEPENDENT_NONPERSISTENT = "independent_nonpersistent", "独立非持久"

    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE, related_name="disks", verbose_name="所属虚拟机")

    # 磁盘标识
    label = models.CharField(max_length=128, verbose_name="磁盘标签", help_text="磁盘标签，如 Hard disk 1")
    device_key = models.IntegerField(verbose_name="设备键", help_text="vSphere 设备键")
    unit_number = models.IntegerField(verbose_name="单元编号", help_text="SCSI 控制器单元编号")

    # 磁盘文件
    datastore_name = models.CharField(max_length=256, verbose_name="数据存储", help_text="磁盘所在数据存储")
    file_path = models.CharField(max_length=512, verbose_name="文件路径", help_text="VMDK 文件路径")

    # 磁盘配置
    capacity_gb = models.IntegerField(verbose_name="磁盘容量", help_text="磁盘容量，单位 GB")
    disk_type = models.CharField(
        max_length=32, choices=DiskType.choices, default=DiskType.THIN, verbose_name="磁盘类型", help_text="置备类型"
    )
    disk_mode = models.CharField(
        max_length=64,
        choices=DiskMode.choices,
        default=DiskMode.PERSISTENT,
        verbose_name="磁盘模式",
        help_text="磁盘持久化模式",
    )

    # 存储使用
    used_gb = models.IntegerField(verbose_name="已用空间", default=0, help_text="实际占用空间，单位 GB")

    # SCSI 控制器
    controller_key = models.IntegerField(verbose_name="控制器键", help_text="SCSI 控制器键")
    controller_type = models.CharField(
        max_length=64, verbose_name="控制器类型", blank=True, null=True, help_text="SCSI 控制器类型"
    )

    # 其他配置
    shares = models.IntegerField(verbose_name="份额", default=1000, help_text="磁盘 I/O 份额")
    extra_config = models.JSONField(verbose_name="扩展配置", default=dict, blank=True, help_text="其他磁盘配置")

    class Meta:
        db_table = "virt_vm_disk"
        verbose_name = "虚拟机磁盘"
        verbose_name_plural = verbose_name
        ordering = ["unit_number"]
        unique_together = [["vm", "device_key"]]

    def __str__(self):
        return f"{self.vm.name} - {self.label}"


class VMNetwork(DbUuidModel):
    """虚拟机网络"""

    class NetworkType(models.TextChoices):
        """网络类型"""

        PORTGROUP = "portgroup", "标准端口组"
        DVPORTGROUP = "dvportgroup", "分布式端口组"

    class AdapterType(models.TextChoices):
        """网卡类型"""

        E1000 = "e1000", "E1000"
        E1000E = "e1000e", "E1000E"
        VMXNET2 = "vmxnet2", "VMXNET 2"
        VMXNET3 = "vmxnet3", "VMXNET 3"

    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE, related_name="networks", verbose_name="所属虚拟机")

    # 网络标识
    label = models.CharField(max_length=128, verbose_name="网卡标签", help_text="网卡标签，如 Network adapter 1")
    device_key = models.IntegerField(verbose_name="设备键", help_text="vSphere 设备键")

    # 网络配置
    network_name = models.CharField(max_length=256, verbose_name="网络名称", help_text="端口组或网络名称")
    network_type = models.CharField(
        max_length=32, choices=NetworkType.choices, verbose_name="网络类型", help_text="网络类型"
    )
    adapter_type = models.CharField(
        max_length=32,
        choices=AdapterType.choices,
        default=AdapterType.VMXNET3,
        verbose_name="网卡类型",
        help_text="虚拟网卡类型",
    )

    # MAC 地址
    mac_address = models.CharField(max_length=64, verbose_name="MAC 地址", help_text="网卡 MAC 地址")
    mac_type = models.CharField(
        max_length=32, verbose_name="MAC 类型", blank=True, null=True, help_text="MAC 地址分配类型（手动/自动）"
    )

    # IP 配置
    ip_address = models.GenericIPAddressField(verbose_name="IP 地址", null=True, blank=True, help_text="分配的 IP 地址")
    netmask = models.CharField(max_length=64, verbose_name="子网掩码", blank=True, null=True, help_text="子网掩码")
    gateway = models.GenericIPAddressField(verbose_name="网关", null=True, blank=True, help_text="默认网关")

    # 连接状态
    connected = models.BooleanField(verbose_name="已连接", default=True, help_text="网卡是否已连接")
    start_connected = models.BooleanField(verbose_name="启动时连接", default=True, help_text="虚拟机启动时是否连接网卡")

    extra_config = models.JSONField(verbose_name="扩展配置", default=dict, blank=True, help_text="其他网络配置")

    class Meta:
        db_table = "virt_vm_network"
        verbose_name = "虚拟机网络"
        verbose_name_plural = verbose_name
        ordering = ["device_key"]
        unique_together = [["vm", "device_key"]]

    def __str__(self):
        return f"{self.vm.name} - {self.label}"


class VMSnapshot(DbUuidModel, DbAuditModel):
    """虚拟机快照"""

    vm = models.ForeignKey(
        VirtualMachine, on_delete=models.CASCADE, related_name="snapshots", verbose_name="所属虚拟机"
    )

    # 快照信息
    name = models.CharField(max_length=256, verbose_name="快照名称", help_text="快照显示名称")
    snapshot_id = models.IntegerField(verbose_name="快照 ID", help_text="vSphere 快照 ID")

    # 层级关系
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="父快照",
        help_text="父快照（用于快照树）",
    )

    # 快照详情
    description = models.TextField(verbose_name="快照描述", blank=True, null=True, help_text="快照描述信息")
    is_current = models.BooleanField(verbose_name="当前快照", default=False, help_text="是否为当前快照")
    is_quiesced = models.BooleanField(
        verbose_name="静默快照", default=False, help_text="是否为静默快照（暂停虚拟机文件系统）"
    )
    is_memory = models.BooleanField(verbose_name="内存快照", default=False, help_text="是否包含虚拟机内存")

    # 快照大小
    size_mb = models.BigIntegerField(verbose_name="快照大小", default=0, help_text="快照占用空间，单位 MB")

    # 快照时虚拟机状态
    power_state_on_snapshot = models.CharField(
        max_length=32, verbose_name="快照时电源状态", blank=True, null=True, help_text="创建快照时的虚拟机电源状态"
    )

    snapshot_time = models.DateTimeField(verbose_name="快照时间", help_text="快照创建时间")

    class Meta:
        db_table = "virt_vm_snapshot"
        verbose_name = "虚拟机快照"
        verbose_name_plural = verbose_name
        ordering = ["-snapshot_time"]
        indexes = [
            models.Index(fields=["vm", "is_current"]),
        ]

    def __str__(self):
        return f"{self.vm.name} - {self.name}"
