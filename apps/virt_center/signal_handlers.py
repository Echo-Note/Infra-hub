#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心信号处理器
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.common.utils import get_logger
from apps.virt_center.models import Platform
from apps.virt_center.notifications import (
    PlatformStatusChangedMessage,
    PlatformSyncFailedMessage,
    PlatformSyncSuccessMessage,
)
from apps.virt_center.signal import platform_status_changed, platform_sync_completed, platform_sync_failed

logger = get_logger(__name__)


@receiver(post_save, sender=Platform)
def auto_sync_platform_on_created(sender, instance, created, **kwargs):
    """
    平台创建时自动触发同步任务

    Args:
        sender: 发送信号的模型类
        instance: Platform 实例
        created: 是否为新创建
    """
    if not created:
        return

    # 只有启用的平台才自动同步
    if not instance.is_active:
        logger.info(f"平台 {instance.name} 未启用，跳过自动同步")
        return

    # 检查是否有认证凭据
    if not hasattr(instance, "credential") or not instance.credential:
        logger.warning(f"平台 {instance.name} 没有配置认证凭据，跳过自动同步")
        return

    try:
        # 延迟导入避免循环依赖
        from apps.virt_center.tasks import sync_all_platform_data

        # 异步执行同步任务
        result = sync_all_platform_data.delay(str(instance.id))
        logger.info(f"平台 {instance.name} 创建成功，已触发自动同步任务: {result.id}")

    except Exception as e:
        logger.error(f"触发平台 {instance.name} 自动同步失败: {str(e)}")


@receiver(platform_sync_completed)
def on_platform_sync_completed(sender, platform_id, platform_name, sync_result, **kwargs):
    """
    平台同步完成处理

    - 发送成功通知
    - 记录审计日志
    - 更新统计信息
    """
    logger.info(f"平台 {platform_name} 同步完成: {sync_result.get('sync_time')}")

    # 发送同步成功通知
    try:
        PlatformSyncSuccessMessage(platform_name, sync_result).publish()
        logger.debug(f"已发送平台 {platform_name} 同步成功通知")
    except Exception as e:
        logger.error(f"发送同步成功通知失败: {str(e)}")


@receiver(platform_sync_failed)
def on_platform_sync_failed(sender, platform_id, platform_name, error, **kwargs):
    """
    平台同步失败处理

    - 发送告警通知
    - 记录错误日志
    - 更新平台状态
    """
    logger.error(f"平台 {platform_name} 同步失败: {error}")

    # 发送同步失败告警
    try:
        PlatformSyncFailedMessage(platform_name, error).publish()
        logger.debug(f"已发送平台 {platform_name} 同步失败告警")
    except Exception as e:
        logger.error(f"发送同步失败告警失败: {str(e)}")


@receiver(platform_status_changed)
def on_platform_status_changed(sender, platform_id, old_status, new_status, **kwargs):
    """
    平台状态变化处理

    - 发送状态变化通知
    - 记录状态变更历史
    """
    logger.info(f"平台状态变化: {old_status} -> {new_status}")

    # 发送状态变化通知
    try:
        # 获取平台名称
        platform = Platform.objects.get(id=platform_id)
        PlatformStatusChangedMessage(platform.name, old_status, new_status).publish()
        logger.debug(f"已发送平台 {platform.name} 状态变化通知")
    except Platform.DoesNotExist:
        logger.warning(f"平台 {platform_id} 不存在，无法发送状态变化通知")
    except Exception as e:
        logger.error(f"发送状态变化通知失败: {str(e)}")
