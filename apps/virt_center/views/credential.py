#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
平台凭据管理视图
"""

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from apps.common.core.modelset import BaseModelSet
from apps.common.core.response import ApiResponse
from apps.common.swagger.utils import get_default_response_schema
from apps.virt_center.filters import PlatformCredentialFilter
from apps.virt_center.models import PlatformCredential
from apps.virt_center.serializers import PlatformCredentialSerializer


class PlatformCredentialViewSet(BaseModelSet):
    """平台凭据管理视图集"""

    queryset = PlatformCredential.objects.all()
    serializer_class = PlatformCredentialSerializer
    ordering_fields = ["created_time", "updated_time"]
    # search_fields 会覆盖 SearchFieldsAction 的 search_fields 方法，需要移除
    # 搜索功能由 filterset_class 提供
    filterset_class = PlatformCredentialFilter

    @extend_schema(responses=get_default_response_schema())
    @action(methods=["GET"], detail=False, url_path="by-platform/(?P<platform_id>[^/.]+)")
    def by_platform(self, request, platform_id=None):
        """根据平台ID获取凭据"""
        try:
            credential = PlatformCredential.objects.get(platform_id=platform_id)
            serializer = self.get_serializer(credential)
            return ApiResponse(data=serializer.data, msg=_("Get credential success"))
        except PlatformCredential.DoesNotExist:
            return ApiResponse(
                code=1001,
                msg=_("Credential not found"),
                data={"platform_id": platform_id},
            )
