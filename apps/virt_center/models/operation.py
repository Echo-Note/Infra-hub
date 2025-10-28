#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
操作记录和任务模型
"""

from django.conf import settings
from django.db import models

from apps.common.core.models import DbAuditModel, DbUuidModel

from .platform import Platform


class OperationLog(DbUuidModel):
    """操作日志"""

    class OperationType(models.TextChoices):
        """操作类型"""

        VM_CREATE = "vm_create", "创建虚拟机"
        VM_DELETE = "vm_delete", "删除虚拟机"
        VM_START = "vm_start", "启动虚拟机"
        VM_STOP = "vm_stop", "停止虚拟机"
        VM_RESTART = "vm_restart", "重启虚拟机"
        VM_SUSPEND = "vm_suspend", "挂起虚拟机"
        VM_SNAPSHOT = "vm_snapshot", "创建快照"
        VM_CLONE = "vm_clone", "克隆虚拟机"
        SYNC_DATA = "sync_data", "同步数据"
        OTHER = "other", "其他操作"

    class Status(models.IntegerChoices):
        """操作状态"""

        PENDING = 0, "等待中"
        RUNNING = 1, "执行中"
        SUCCESS = 2, "成功"
        FAILED = 3, "失败"
        CANCELLED = 4, "已取消"

    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name="operation_logs",
        verbose_name="所属平台",
        null=True,
        blank=True,
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="virt_operations",
        verbose_name="操作人",
    )

    operation_type = models.CharField(max_length=64, choices=OperationType.choices, verbose_name="操作类型")
    target_type = models.CharField(
        max_length=64, verbose_name="目标类型", help_text="操作对象类型：vm、host、datastore等"
    )
    target_id = models.CharField(max_length=128, verbose_name="目标 ID", help_text="操作对象的 ID")
    target_name = models.CharField(max_length=256, verbose_name="目标名称", help_text="操作对象名称")

    status = models.SmallIntegerField(
        choices=Status.choices, default=Status.PENDING, verbose_name="状态", db_index=True
    )
    result = models.TextField(verbose_name="执行结果", blank=True, null=True, help_text="操作执行结果")
    error_message = models.TextField(verbose_name="错误信息", blank=True, null=True, help_text="失败时的错误信息")

    # 操作参数
    parameters = models.JSONField(verbose_name="操作参数", default=dict, blank=True, help_text="操作参数 JSON")

    # 时间信息
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间", null=True, blank=True, help_text="操作完成时间")
    duration_seconds = models.IntegerField(verbose_name="执行时长", default=0, help_text="执行时长，单位秒")

    class Meta:
        db_table = "virt_operation_log"
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["platform", "-start_time"]),
            models.Index(fields=["operator", "-start_time"]),
            models.Index(fields=["operation_type", "-start_time"]),
        ]

    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.target_name}"


class OperationTask(DbUuidModel, DbAuditModel):
    """操作任务（异步任务）"""

    class TaskType(models.TextChoices):
        """任务类型"""

        SYNC_PLATFORM = "sync_platform", "同步平台数据"
        SYNC_HOSTS = "sync_hosts", "同步主机"
        SYNC_VMS = "sync_vms", "同步虚拟机"
        SYNC_DATASTORES = "sync_datastores", "同步存储"
        COLLECT_METRICS = "collect_metrics", "采集监控指标"
        BACKUP_VM = "backup_vm", "备份虚拟机"
        BATCH_OPERATION = "batch_operation", "批量操作"

    class Status(models.IntegerChoices):
        """任务状态"""

        PENDING = 0, "等待中"
        RUNNING = 1, "执行中"
        SUCCESS = 2, "成功"
        FAILED = 3, "失败"
        CANCELLED = 4, "已取消"

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="tasks", verbose_name="所属平台", null=True, blank=True
    )

    task_type = models.CharField(max_length=64, choices=TaskType.choices, verbose_name="任务类型")
    task_name = models.CharField(max_length=256, verbose_name="任务名称", help_text="任务描述性名称")
    status = models.SmallIntegerField(
        choices=Status.choices, default=Status.PENDING, verbose_name="任务状态", db_index=True
    )

    # Celery 任务 ID
    celery_task_id = models.CharField(
        max_length=128, verbose_name="Celery 任务 ID", blank=True, null=True, help_text="Celery 任务 ID"
    )

    # 任务参数和结果
    parameters = models.JSONField(verbose_name="任务参数", default=dict, blank=True)
    result = models.JSONField(verbose_name="执行结果", default=dict, blank=True, help_text="任务执行结果")
    error_message = models.TextField(verbose_name="错误信息", blank=True, null=True)

    # 进度信息
    progress = models.IntegerField(verbose_name="执行进度", default=0, help_text="任务进度 0-100")
    current_step = models.CharField(max_length=256, verbose_name="当前步骤", blank=True, null=True)

    # 时间信息
    scheduled_time = models.DateTimeField(verbose_name="计划执行时间", null=True, blank=True)
    start_time = models.DateTimeField(verbose_name="开始时间", null=True, blank=True)
    end_time = models.DateTimeField(verbose_name="结束时间", null=True, blank=True)
    duration_seconds = models.IntegerField(verbose_name="执行时长", default=0, help_text="执行时长，单位秒")

    class Meta:
        db_table = "virt_operation_task"
        verbose_name = "操作任务"
        verbose_name_plural = verbose_name
        ordering = ["-created_time"]
        indexes = [
            models.Index(fields=["platform", "-created_time"]),
            models.Index(fields=["status", "-created_time"]),
            models.Index(fields=["task_type", "-created_time"]),
            models.Index(fields=["celery_task_id"]),
        ]

    def __str__(self):
        return f"{self.task_name} - {self.get_status_display()}"
