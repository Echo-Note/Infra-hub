#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
存储相关模型
vSphere 数据存储管理
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.core.models import DbAuditModel, DbUuidModel

from .host import Host
from .platform import Platform


class DataStore(DbUuidModel, DbAuditModel):
    """数据存储（Datastore）"""

    class DataStoreType(models.TextChoices):
        """数据存储类型"""

        VMFS = "vmfs", "VMFS"
        NFS = "nfs", "NFS"
        NFS41 = "nfs41", "NFS 4.1"
        VSAN = "vsan", "vSAN"
        VVOL = "vvol", "vVol"
        LOCAL = "local", "本地存储"

    class AccessMode(models.TextChoices):
        """访问模式"""

        READ_WRITE = "readWrite", "读写"
        READ_ONLY = "readOnly", "只读"

    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name="datastores",
        verbose_name="所属平台",
        help_text="所属 vCenter 平台",
    )

    # 基本信息
    name = models.CharField(max_length=256, verbose_name="存储名称", help_text="数据存储显示名称", db_index=True)
    mo_ref = models.CharField(
        max_length=128, verbose_name="MO 引用", blank=True, null=True, help_text="vSphere Managed Object Reference ID"
    )
    url = models.CharField(max_length=512, verbose_name="存储 URL", blank=True, null=True, help_text="数据存储URL")

    # 存储类型和配置
    datastore_type = models.CharField(
        max_length=32, choices=DataStoreType.choices, verbose_name="存储类型", help_text="数据存储类型"
    )
    access_mode = models.CharField(
        max_length=32,
        choices=AccessMode.choices,
        default=AccessMode.READ_WRITE,
        verbose_name="访问模式",
        help_text="访问权限",
    )

    # 位置信息
    datacenter_name = models.CharField(
        max_length=128, verbose_name="数据中心", blank=True, null=True, help_text="所属数据中心"
    )
    cluster_name = models.CharField(
        max_length=128, verbose_name="集群名称", blank=True, null=True, help_text="所属集群"
    )

    # 容量信息（单位：GB）
    capacity_gb = models.BigIntegerField(verbose_name="总容量", default=0, help_text="总容量，单位 GB")
    free_gb = models.BigIntegerField(verbose_name="可用容量", default=0, help_text="可用容量，单位 GB")
    uncommitted_gb = models.BigIntegerField(
        verbose_name="未提交容量", default=0, help_text="未提交的虚拟机磁盘空间，单位 GB"
    )

    # 使用统计
    vm_count = models.IntegerField(verbose_name="虚拟机数量", default=0, help_text="使用该存储的虚拟机数量")
    usage_percent = models.FloatField(
        verbose_name="使用率",
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="存储使用率百分比",
    )

    # NFS 特定配置
    nfs_server = models.CharField(
        max_length=256, verbose_name="NFS 服务器", blank=True, null=True, help_text="NFS 服务器地址"
    )
    nfs_path = models.CharField(
        max_length=512, verbose_name="NFS 路径", blank=True, null=True, help_text="NFS 共享路径"
    )

    # 本地存储特定配置
    local_path = models.CharField(
        max_length=512, verbose_name="本地路径", blank=True, null=True, help_text="本地存储挂载路径"
    )

    # 关联主机
    hosts = models.ManyToManyField(
        Host, related_name="datastores", verbose_name="挂载主机", blank=True, help_text="可访问此存储的主机列表"
    )

    # 状态和性能
    is_accessible = models.BooleanField(verbose_name="可访问", default=True, help_text="数据存储是否可访问")
    is_maintenance = models.BooleanField(verbose_name="维护模式", default=False, help_text="是否处于维护模式")
    multiple_host_access = models.BooleanField(
        verbose_name="多主机访问", default=True, help_text="是否支持多主机同时访问"
    )

    # 管理信息
    is_active = models.BooleanField(verbose_name="启用状态", default=True, help_text="是否启用管理", db_index=True)
    tags = models.JSONField(verbose_name="标签", default=list, blank=True, help_text="自定义标签列表")
    extra_info = models.JSONField(verbose_name="扩展信息", default=dict, blank=True, help_text="其他扩展信息")
    last_sync_time = models.DateTimeField(verbose_name="最后同步", null=True, blank=True, help_text="最后同步时间")

    class Meta:
        db_table = "virt_datastore"
        verbose_name = "数据存储"
        verbose_name_plural = verbose_name
        ordering = ["-created_time"]
        unique_together = [["platform", "name"]]
        indexes = [
            models.Index(fields=["platform", "datastore_type"]),
            models.Index(fields=["platform", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.datastore_type})"

    @property
    def used_gb(self):
        """已使用容量（GB）"""
        return self.capacity_gb - self.free_gb

    @property
    def provisioned_gb(self):
        """已分配容量（GB）"""
        return self.used_gb + self.uncommitted_gb


class StoragePolicy(DbUuidModel, DbAuditModel):
    """存储策略"""

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="storage_policies", verbose_name="所属平台"
    )

    name = models.CharField(max_length=256, verbose_name="策略名称", help_text="存储策略名称")
    policy_id = models.CharField(max_length=128, verbose_name="策略 ID", help_text="vSphere 策略 ID", unique=True)
    description = models.TextField(verbose_name="策略描述", blank=True, null=True, help_text="存储策略描述")

    # 策略规则
    rules = models.JSONField(verbose_name="策略规则", default=dict, blank=True, help_text="策略规则定义")

    # 兼容的数据存储
    compatible_datastores = models.ManyToManyField(
        DataStore, related_name="policies", verbose_name="兼容存储", blank=True, help_text="符合该策略的数据存储"
    )

    is_default = models.BooleanField(verbose_name="默认策略", default=False, help_text="是否为默认存储策略")
    is_active = models.BooleanField(verbose_name="启用状态", default=True, help_text="是否启用")

    class Meta:
        db_table = "virt_storage_policy"
        verbose_name = "存储策略"
        verbose_name_plural = verbose_name
        ordering = ["name"]

    def __str__(self):
        return self.name
