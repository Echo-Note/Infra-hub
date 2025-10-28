#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心 URL 配置
"""

from rest_framework.routers import SimpleRouter

from apps.virt_center.views import PlatformCredentialViewSet, PlatformViewSet, SyncTaskViewSet

app_name = "virt_center"

# 创建路由器，设置 trailing_slash=False 允许 URL 末尾不带斜杠
router = SimpleRouter(trailing_slash=False)

# 注册视图集
router.register("platforms", PlatformViewSet, basename="platform")
router.register("credentials", PlatformCredentialViewSet, basename="credential")
router.register("sync", SyncTaskViewSet, basename="sync-task")

urlpatterns = router.urls
