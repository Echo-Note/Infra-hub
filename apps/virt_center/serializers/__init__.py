#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心序列化器
"""

from .credential import PlatformCredentialSerializer
from .host import (
    HostDetailSerializer,
    HostListSerializer,
    HostNetworkSerializer,
    HostOperationSerializer,
    HostResourceSerializer,
    HostSerializer,
)
from .platform import PlatformSerializer, SyncTaskSerializer
from .vm import (
    VirtualMachineDetailSerializer,
    VirtualMachineListSerializer,
    VirtualMachineSerializer,
    VMDiskSerializer,
    VMNetworkSerializer,
    VMOperationSerializer,
    VMSnapshotSerializer,
)

__all__ = [
    "PlatformSerializer",
    "PlatformCredentialSerializer",
    "SyncTaskSerializer",
    # Host
    "HostSerializer",
    "HostListSerializer",
    "HostDetailSerializer",
    "HostResourceSerializer",
    "HostNetworkSerializer",
    "HostOperationSerializer",
    # VM
    "VirtualMachineSerializer",
    "VirtualMachineListSerializer",
    "VirtualMachineDetailSerializer",
    "VMDiskSerializer",
    "VMNetworkSerializer",
    "VMSnapshotSerializer",
    "VMOperationSerializer",
]
