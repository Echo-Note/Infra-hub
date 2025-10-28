#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心视图
"""

from .platform import PlatformViewSet
from .sync import SyncTaskViewSet

__all__ = [
    "PlatformViewSet",
    "SyncTaskViewSet",
]
