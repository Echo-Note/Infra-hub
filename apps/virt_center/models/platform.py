#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化平台模型
主要支持 VMware vSphere/vCenter，预留其他平台扩展性
"""

from django.db import models

from apps.common.core.models import DbAuditModel, DbUuidModel
from apps.common.fields import EncryptedCharField, EncryptedTextField


class Platform(DbUuidModel, DbAuditModel):
    """虚拟化平台配置"""

    class PlatformType(models.TextChoices):
        """平台类型"""

        VCENTER = "vcenter", "VMware vCenter"
        ESXI = "esxi", "VMware ESXi"
        # 预留其他平台类型
        KVM = "kvm", "KVM"
        PROXMOX = "proxmox", "Proxmox VE"

    class Status(models.IntegerChoices):
        """连接状态"""

        DISCONNECTED = 0, "未连接"
        CONNECTED = 1, "已连接"
        ERROR = 2, "连接异常"
        MAINTENANCE = 3, "维护中"

    name = models.CharField(
        max_length=128,
        verbose_name="平台名称",
        help_text="虚拟化平台的显示名称",
        unique=True,
        db_index=True,
    )
    platform_type = models.CharField(
        max_length=32,
        choices=PlatformType.choices,
        default=PlatformType.VCENTER,
        verbose_name="平台类型",
        help_text="虚拟化平台类型，推荐使用 vCenter 管理多台 ESXi",
        db_index=True,
    )
    host = models.CharField(max_length=256, verbose_name="主机地址", help_text="vCenter/ESXi 的 IP 地址或域名")
    port = models.IntegerField(verbose_name="端口", default=443, help_text="vCenter/ESXi HTTPS 端口，默认 443")
    is_ssl = models.BooleanField(verbose_name="启用 SSL", default=True, help_text="是否使用 HTTPS 连接")
    ssl_verify = models.BooleanField(verbose_name="验证 SSL 证书", default=False, help_text="是否验证 SSL 证书有效性")
    status = models.SmallIntegerField(
        choices=Status.choices, default=Status.DISCONNECTED, verbose_name="连接状态", db_index=True
    )
    is_active = models.BooleanField(verbose_name="启用状态", default=True, help_text="是否启用该平台", db_index=True)

    # 地理位置信息
    region = models.CharField(
        max_length=64, verbose_name="所属区域", blank=True, null=True, help_text="数据中心所在区域，如：北京、上海"
    )
    datacenter = models.CharField(
        max_length=128, verbose_name="数据中心", blank=True, null=True, help_text="vSphere 数据中心名称"
    )

    # vSphere 版本信息
    version = models.CharField(max_length=64, verbose_name="版本", blank=True, null=True, help_text="vSphere 版本号")
    build = models.CharField(max_length=64, verbose_name="构建号", blank=True, null=True, help_text="vSphere 构建号")

    # 标签和扩展配置
    tags = models.JSONField(verbose_name="标签", default=dict, blank=True, help_text="自定义标签，JSON 格式")
    extra_config = models.JSONField(
        verbose_name="扩展配置", default=dict, blank=True, help_text="额外配置信息，JSON 格式"
    )

    # 统计信息
    total_hosts = models.IntegerField(verbose_name="主机总数", default=0, help_text="该平台下的 ESXi 主机总数")
    total_vms = models.IntegerField(verbose_name="虚拟机总数", default=0, help_text="该平台下的虚拟机总数")
    total_clusters = models.IntegerField(verbose_name="集群总数", default=0, help_text="vSphere 集群总数")
    last_sync_time = models.DateTimeField(
        verbose_name="最后同步时间", null=True, blank=True, help_text="最后一次同步数据的时间"
    )

    class Meta:
        db_table = "virt_platform"
        verbose_name = "虚拟化平台"
        verbose_name_plural = verbose_name
        ordering = ["-created_time"]

    def __str__(self):
        return f"{self.name} ({self.get_platform_type_display()})"

    @property
    def connection_url(self):
        """获取连接URL"""
        protocol = "https" if self.is_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"


class PlatformCredential(DbUuidModel, DbAuditModel):
    """平台认证凭据"""

    class AuthType(models.TextChoices):
        """认证类型"""

        PASSWORD = "password", "用户名密码"
        TOKEN = "token", "API Token"
        SESSION = "session", "会话认证"

    platform = models.OneToOneField(
        Platform, on_delete=models.CASCADE, related_name="credential", verbose_name="所属平台"
    )
    auth_type = models.CharField(
        max_length=32,
        choices=AuthType.choices,
        default=AuthType.PASSWORD,
        verbose_name="认证类型",
        help_text="vSphere 推荐使用用户名密码认证",
    )
    username = models.CharField(
        max_length=128, verbose_name="用户名", blank=True, null=True, help_text="vCenter/ESXi 登录用户名"
    )
    password = EncryptedCharField(
        max_length=128, verbose_name="密码", blank=True, null=True, help_text="vCenter/ESXi 登录密码（自动加密存储）"
    )
    token = EncryptedTextField(
        verbose_name="API Token", blank=True, null=True, help_text="API 访问令牌（自动加密存储）"
    )
    session_id = EncryptedCharField(
        max_length=128, verbose_name="会话 ID", blank=True, null=True, help_text="当前会话 ID（自动加密存储）"
    )
    session_expires = models.DateTimeField(verbose_name="会话过期时间", null=True, blank=True, help_text="会话过期时间")
    extra_data = models.JSONField(
        verbose_name="扩展数据", default=dict, blank=True, help_text="其他认证相关数据，JSON 格式"
    )

    class Meta:
        db_table = "virt_platform_credential"
        verbose_name = "平台认证凭据"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.platform.name} - {self.get_auth_type_display()}"
