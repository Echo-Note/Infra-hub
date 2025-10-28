#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心模型
"""

from .host import Host, HostNetwork, HostResource
from .monitor import HostMetrics, VMMetrics
from .operation import OperationLog, OperationTask
from .platform import Platform, PlatformCredential
from .storage import DataStore
from .template import VMTemplate
from .vm import VirtualMachine, VMDisk, VMNetwork, VMSnapshot

__all__ = [
    # 平台管理
    "Platform",
    "PlatformCredential",
    # 主机管理
    "Host",
    "HostResource",
    "HostNetwork",
    # 虚拟机管理
    "VirtualMachine",
    "VMSnapshot",
    "VMDisk",
    "VMNetwork",
    # 存储管理
    "DataStore",
    # 模板管理
    "VMTemplate",
    # 监控管理
    "HostMetrics",
    "VMMetrics",
    # 操作管理
    "OperationLog",
    "OperationTask",
]
