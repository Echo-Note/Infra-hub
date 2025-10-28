#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心工具模块
"""

from .vsphere_client import VSphereClient, get_vsphere_client

__all__ = ["VSphereClient", "get_vsphere_client"]
