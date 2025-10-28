#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
监控指标模型
用于存储时序监控数据
"""

from django.db import models

from apps.common.core.models import DbUuidModel

from .host import Host
from .vm import VirtualMachine

"""
时许数据应该存储在时序数据库中，如 InfluxDB、TimescaleDB 等。
这里为了简化设计，直接使用关系型数据库存储，适用于小规模环境。
如果需要使用时序数据库，可以将此模型作为 ORM 映射，或编写专门的存储接口。
推荐使用 TimescaleDB 存储时序数据，具有时序数据库的所有优点，同时兼容 PostgreSQL 的所有特性。

TimescaleDB 的 Django 支持
https://github.com/jamessewell/django-timescaledb.git
"""


class BaseMetrics(DbUuidModel):
    """监控指标抽象基类"""

    # CPU 指标
    cpu_usage_percent = models.FloatField(verbose_name="CPU 使用率", default=0.0, help_text="CPU 使用率百分比")
    cpu_usage_mhz = models.IntegerField(verbose_name="CPU 使用频率", default=0, help_text="已使用 CPU 频率，单位 MHz")
    cpu_ready_percent = models.FloatField(verbose_name="CPU 就绪率", default=0.0, help_text="CPU 就绪时间百分比")

    # 内存指标
    memory_usage_percent = models.FloatField(verbose_name="内存使用率", default=0.0, help_text="内存使用率百分比")
    memory_used_mb = models.BigIntegerField(verbose_name="已用内存", default=0, help_text="已使用内存，单位 MB")
    memory_active_mb = models.BigIntegerField(verbose_name="活动内存", default=0, help_text="活动内存，单位 MB")
    memory_consumed_mb = models.BigIntegerField(verbose_name="消耗内存", default=0, help_text="虚拟机消耗内存，单位 MB")
    memory_balloon_mb = models.BigIntegerField(verbose_name="气球内存", default=0, help_text="气球驱动内存，单位 MB")

    # 网络指标
    network_rx_kbps = models.BigIntegerField(
        verbose_name="网络接收速率", default=0, help_text="网络接收速率，单位 KBps"
    )
    network_tx_kbps = models.BigIntegerField(
        verbose_name="网络发送速率", default=0, help_text="网络发送速率，单位 KBps"
    )
    network_rx_packets = models.BigIntegerField(verbose_name="接收包数", default=0, help_text="网络接收包数")
    network_tx_packets = models.BigIntegerField(verbose_name="发送包数", default=0, help_text="网络发送包数")

    # 磁盘 I/O 指标
    disk_read_kbps = models.BigIntegerField(verbose_name="磁盘读速率", default=0, help_text="磁盘读取速率，单位 KBps")
    disk_write_kbps = models.BigIntegerField(verbose_name="磁盘写速率", default=0, help_text="磁盘写入速率，单位 KBps")
    disk_read_iops = models.IntegerField(verbose_name="磁盘读 IOPS", default=0, help_text="磁盘读取 IOPS")
    disk_write_iops = models.IntegerField(verbose_name="磁盘写 IOPS", default=0, help_text="磁盘写入 IOPS")
    disk_latency_ms = models.FloatField(verbose_name="磁盘延迟", default=0.0, help_text="磁盘延迟，单位毫秒")

    # 采集时间
    collected_at = models.DateTimeField(verbose_name="采集时间", db_index=True, help_text="指标采集时间")

    class Meta:
        abstract = True


class HostMetrics(BaseMetrics):
    """主机监控指标"""

    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="metrics", verbose_name="所属主机")

    class Meta:
        db_table = "virt_host_metrics"
        verbose_name = "主机监控指标"
        verbose_name_plural = verbose_name
        ordering = ["-collected_at"]
        indexes = [
            models.Index(fields=["host", "-collected_at"]),
        ]

    def __str__(self):
        return f"{self.host.name} - {self.collected_at}"


class VMMetrics(BaseMetrics):
    """虚拟机监控指标"""

    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE, related_name="metrics", verbose_name="所属虚拟机")

    # 虚拟机特有的内存指标
    memory_swapped_mb = models.BigIntegerField(
        verbose_name="交换内存", default=0, help_text="交换到磁盘的内存，单位 MB"
    )

    class Meta:
        db_table = "virt_vm_metrics"
        verbose_name = "虚拟机监控指标"
        verbose_name_plural = verbose_name
        ordering = ["-collected_at"]
        indexes = [
            models.Index(fields=["vm", "-collected_at"]),
        ]

    def __str__(self):
        return f"{self.vm.name} - {self.collected_at}"
