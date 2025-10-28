#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟机模板相关模型
"""

from django.db import models

from apps.common.core.models import DbAuditModel, DbUuidModel

from .platform import Platform


class VMTemplate(DbUuidModel, DbAuditModel):
    """虚拟机模板"""

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="vm_templates", verbose_name="所属平台"
    )

    # 基本信息
    name = models.CharField(max_length=256, verbose_name="模板名称", help_text="虚拟机模板名称", db_index=True)
    display_name = models.CharField(
        max_length=256, verbose_name="显示名称", blank=True, null=True, help_text="显示名称"
    )

    # vSphere 标识
    mo_ref = models.CharField(max_length=128, verbose_name="MO 引用", blank=True, null=True, help_text="vSphere MO引用")
    uuid = models.CharField(
        max_length=128, verbose_name="UUID", blank=True, null=True, unique=True, help_text="模板 UUID"
    )

    # 模板配置
    os_type = models.CharField(
        max_length=64, verbose_name="操作系统类型", blank=True, null=True, help_text="操作系统类型"
    )
    cpu_count = models.IntegerField(verbose_name="CPU 数量", default=1, help_text="vCPU 数量")
    memory_mb = models.IntegerField(verbose_name="内存大小", default=1024, help_text="内存大小，单位 MB")
    disk_gb = models.IntegerField(verbose_name="磁盘大小", default=20, help_text="磁盘大小，单位 GB")

    # 模板描述
    category = models.CharField(max_length=128, verbose_name="模板分类", blank=True, null=True, help_text="模板分类")
    is_active = models.BooleanField(verbose_name="启用状态", default=True, help_text="是否启用", db_index=True)
    tags = models.JSONField(verbose_name="标签", default=list, blank=True, help_text="标签列表")

    class Meta:
        db_table = "virt_vm_template"
        verbose_name = "虚拟机模板"
        verbose_name_plural = verbose_name
        ordering = ["-created_time"]
        unique_together = [["platform", "name"]]

    def __str__(self):
        return self.name
