from rest_framework import viewsets, filters
from apps.common.core.modelset import BaseModelSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Host
from ..serializers.hosts import HostSerializer
from apps.virt_center.filters import EsxiformFilter


class EsxiHostViewSet(BaseModelSet):
    """
    ESXi宿主机视图集
    提供完整的CRUD操作和过滤搜索功能
    """
    queryset = Host.objects.all()
    serializer_class = HostSerializer
    permission_classes = [IsAuthenticated]

    # 过滤和搜索配置
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'power_state', 'is_active', 'platform']
    #search_fields = ['name', 'hostname', 'ip_address']
    ordering_fields = ['created_time', 'name', 'status']
    ordering = ['-created_time']
    filterset_class = EsxiformFilter
