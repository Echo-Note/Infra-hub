#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心视图
"""

from .credential import PlatformCredentialViewSet
from .host import HostViewSet
from .platform import PlatformViewSet
from .sync import SyncTaskViewSet
from .vm import VirtualMachineViewSet

__all__ = [
    "PlatformViewSet",
    "PlatformCredentialViewSet",
    "SyncTaskViewSet",
    "HostViewSet",
    "VirtualMachineViewSet",
]
