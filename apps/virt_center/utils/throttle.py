#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
vSphere 同步任务限流工具
"""

from django.core.cache import cache

from apps.common.utils import get_logger

logger = get_logger(__name__)


class SyncTaskThrottle:
    """同步任务限流工具"""

    RATE_LIMIT_KEY_TMPL = "virt_center_sync_rate_limit_{}"
    RATE_LIMIT_SECONDS = 300  # 5分钟限流

    def __init__(self, platform_id: str, rate_limit_seconds: int = None):
        """
        初始化限流工具

        Args:
            platform_id: 平台ID
            rate_limit_seconds: 限流时间（秒），默认300秒
        """
        self.platform_id = platform_id
        self.rate_limit_key = self.RATE_LIMIT_KEY_TMPL.format(platform_id)
        self.rate_limit_seconds = rate_limit_seconds or self.RATE_LIMIT_SECONDS

    def is_allowed(self) -> bool:
        """
        检查是否允许执行任务

        Returns:
            bool: True 允许，False 限流中
        """
        return not cache.get(self.rate_limit_key)

    def get_remaining_time(self) -> int:
        """
        获取剩余限流时间

        Returns:
            int: 剩余秒数，0表示不在限流中
        """
        if not cache.get(self.rate_limit_key):
            return 0
        return cache.ttl(self.rate_limit_key) or 0

    def mark_executed(self):
        """标记任务已执行，开始限流"""
        cache.set(self.rate_limit_key, True, self.rate_limit_seconds)
        logger.debug(f"平台 {self.platform_id} 已标记限流 {self.rate_limit_seconds} 秒")

    def clear_limit(self):
        """清除限流标记（用于异常情况）"""
        cache.delete(self.rate_limit_key)
        logger.debug(f"平台 {self.platform_id} 限流标记已清除")

    @classmethod
    def clear_all_limits(cls):
        """清除所有平台的限流标记"""
        pattern = cls.RATE_LIMIT_KEY_TMPL.format("*")
        cache.delete_pattern(pattern)
        logger.info("所有平台限流标记已清除")
