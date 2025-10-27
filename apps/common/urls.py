#!/usr/bin/env python
# -*- coding:utf-8 -*-
# project : server
# filename : urls
# author : ly_13
# date : 6/6/2023
from django.urls import path, re_path

from apps.common.api.common import CountryListAPIView, HealthCheckAPIView, ResourcesIDCacheAPIView

app_name = "common"

urlpatterns = [
    path("resources/cache", ResourcesIDCacheAPIView.as_view(), name="resources-cache"),
    path("countries", CountryListAPIView.as_view(), name="countries"),
    re_path("^api/health", HealthCheckAPIView.as_view(), name="health"),
]
