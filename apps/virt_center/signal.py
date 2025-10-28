#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心自定义信号
"""

from django.dispatch import Signal

# 平台同步完成信号
# 参数: platform_id, platform_name, sync_result
platform_sync_completed = Signal()

# 平台同步失败信号
# 参数: platform_id, platform_name, error
platform_sync_failed = Signal()

# 平台连接状态变化信号
# 参数: platform_id, old_status, new_status
platform_status_changed = Signal()
