from rest_framework import serializers
from ..models import Host, HostResource, HostNetwork


class HostSerializer(serializers.ModelSerializer):
    """
    ESXi宿主机模型序列化器
    """
    platform_type_display = serializers.CharField(source="get_platform_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    connection_url = serializers.CharField(read_only=True)
    class Meta:
        model = Host
        fields = "__all__"
        #table_fields = ["name", "host", "status", "is_active"]
        read_only_fields = (
            "id",
            "created_time",
            "updated_time",
        )


class HostResourceSerializer(serializers.ModelSerializer):
    """
    主机资源详情序列化器
    """

    class Meta:
        model = HostResource
        fields = "__all__"
        read_only_fields = (
            "id",
            "updated_time",
        )


class HostNetworkSerializer(serializers.ModelSerializer):
    """
    主机网络配置序列化器
    """

    class Meta:
        model = HostNetwork
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_time",
            "updated_time",
        )

