#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
vSphere 数据同步模块
将解析后的数据同步到数据库
"""

import logging
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from apps.virt_center.models import DataStore, Host, Platform, VirtualMachine, VMTemplate

logger = logging.getLogger(__name__)


def sync_platform_to_db(platform: Platform, platform_data: Dict[str, Any]) -> Platform:
    """
    同步平台信息到数据库

    Args:
        platform: 平台对象
        platform_data: 平台数据

    Returns:
        更新后的平台对象
    """
    try:
        # 更新平台信息
        platform.version = platform_data.get("version", "")
        platform.build = platform_data.get("build", "")
        platform.datacenter = platform_data.get("datacenter", "")
        platform.total_hosts = platform_data.get("total_hosts", 0)
        platform.total_vms = platform_data.get("total_vms", 0)
        platform.total_clusters = platform_data.get("total_clusters", 0)
        platform.status = platform_data.get("status", 1)
        platform.last_sync_time = timezone.now()

        platform.save(
            update_fields=[
                "version",
                "build",
                "datacenter",
                "total_hosts",
                "total_vms",
                "total_clusters",
                "status",
                "last_sync_time",
                "updated_time",
            ]
        )

        logger.info(f"平台信息已更新: {platform.name}")
        return platform

    except Exception as e:
        logger.error(f"同步平台信息到数据库失败: {str(e)}")
        raise


def sync_host_to_db(platform: Platform, host_data: Dict[str, Any]) -> Host:
    """
    同步主机信息到数据库

    Args:
        platform: 平台对象
        host_data: 主机数据

    Returns:
        主机对象
    """
    try:
        with transaction.atomic():
            # 根据 UUID 查找或创建主机
            host, created = Host.objects.update_or_create(
                platform=platform,
                uuid=host_data["uuid"],
                defaults={
                    "name": host_data["name"],
                    "hostname": host_data.get("hostname", ""),
                    "ip_address": host_data["ip_address"],
                    "mo_ref": host_data.get("mo_ref", ""),
                    "cluster_name": host_data.get("cluster_name", ""),
                    "datacenter_name": host_data.get("datacenter_name", ""),
                    "status": host_data.get("status", 5),
                    "power_state": host_data.get("power_state", "unknown"),
                    "connection_state": host_data.get("connection_state", ""),
                    "vendor": host_data.get("vendor", ""),
                    "model": host_data.get("model", ""),
                    "esxi_version": host_data.get("esxi_version", ""),
                    "esxi_build": host_data.get("esxi_build", ""),
                    "cpu_model": host_data.get("cpu_model", ""),
                    "cpu_cores": host_data.get("cpu_cores", 0),
                    "cpu_threads": host_data.get("cpu_threads", 0),
                    "cpu_sockets": host_data.get("cpu_sockets", 0),
                    "cpu_frequency": host_data.get("cpu_frequency", 0),
                    "memory_total": host_data.get("memory_total", 0),
                    "vm_count": host_data.get("vm_count", 0),
                    "cpu_usage": host_data.get("cpu_usage", 0.0),
                    "memory_usage": host_data.get("memory_usage", 0.0),
                    "in_maintenance": host_data.get("in_maintenance", False),
                    "is_active": True,
                    "last_seen": timezone.now(),
                },
            )

            action = "创建" if created else "更新"
            logger.debug(f"{action}主机: {host.name}")

            return host

    except Exception as e:
        logger.error(f"同步主机到数据库失败 {host_data['name']}: {str(e)}")
        raise


def sync_vm_to_db(platform: Platform, vm_data: Dict[str, Any]) -> VirtualMachine:
    """
    同步虚拟机信息到数据库

    Args:
        platform: 平台对象
        vm_data: 虚拟机数据

    Returns:
        虚拟机对象
    """
    try:
        with transaction.atomic():
            # 获取关联的主机
            host = None
            if vm_data.get("host_name"):
                try:
                    host = Host.objects.get(platform=platform, name=vm_data["host_name"])
                except Host.DoesNotExist:
                    logger.warning(f"未找到主机 {vm_data['host_name']}，虚拟机 {vm_data['name']} 将不关联主机")

            # 根据 UUID 查找或创建虚拟机
            vm, created = VirtualMachine.objects.update_or_create(
                platform=platform,
                uuid=vm_data["uuid"],
                defaults={
                    "host": host,
                    "name": vm_data["name"],
                    "display_name": vm_data.get("display_name", ""),
                    "mo_ref": vm_data.get("mo_ref", ""),
                    "instance_uuid": vm_data.get("instance_uuid", ""),
                    "cluster_name": vm_data.get("cluster_name", ""),
                    "datacenter_name": vm_data.get("datacenter_name", ""),
                    "resource_pool": vm_data.get("resource_pool", ""),
                    "folder": vm_data.get("folder", ""),
                    "status": vm_data.get("status", 0),
                    "power_state": vm_data.get("power_state", "poweredOff"),
                    "connection_state": vm_data.get("connection_state", ""),
                    "os_type": vm_data.get("os_type", "other"),
                    "os_full_name": vm_data.get("os_full_name", ""),
                    "guest_id": vm_data.get("guest_id", ""),
                    "guest_state": vm_data.get("guest_state", ""),
                    "tools_status": vm_data.get("tools_status", ""),
                    "tools_version": vm_data.get("tools_version", ""),
                    "cpu_count": vm_data.get("cpu_count", 1),
                    "cpu_cores_per_socket": vm_data.get("cpu_cores_per_socket", 1),
                    "memory_mb": vm_data.get("memory_mb", 1024),
                    "hardware_version": vm_data.get("hardware_version", ""),
                    "ip_address": vm_data.get("ip_address"),
                    "mac_address": vm_data.get("mac_address", ""),
                    "hostname": vm_data.get("hostname", ""),
                    "disk_count": vm_data.get("disk_count", 0),
                    "total_disk_gb": vm_data.get("total_disk_gb", 0),
                    "cpu_usage_percent": vm_data.get("cpu_usage_percent", 0.0),
                    "memory_usage_percent": vm_data.get("memory_usage_percent", 0.0),
                    "has_snapshots": vm_data.get("has_snapshots", False),
                    "snapshot_count": vm_data.get("snapshot_count", 0),
                    "is_template": vm_data.get("is_template", False),
                    "is_active": True,
                    "boot_time": vm_data.get("boot_time"),
                    "last_seen": timezone.now(),
                },
            )

            action = "创建" if created else "更新"
            logger.debug(f"{action}虚拟机: {vm.name}")

            return vm

    except Exception as e:
        logger.error(f"同步虚拟机到数据库失败 {vm_data['name']}: {str(e)}")
        raise


def sync_datastore_to_db(platform: Platform, ds_data: Dict[str, Any]) -> DataStore:
    """
    同步数据存储信息到数据库

    Args:
        platform: 平台对象
        ds_data: 数据存储数据

    Returns:
        数据存储对象
    """
    try:
        with transaction.atomic():
            # 根据名称查找或创建数据存储
            datastore, created = DataStore.objects.update_or_create(
                platform=platform,
                name=ds_data["name"],
                defaults={
                    "mo_ref": ds_data.get("mo_ref", ""),
                    "url": ds_data.get("url", ""),
                    "datastore_type": ds_data.get("datastore_type", "vmfs"),
                    "access_mode": ds_data.get("access_mode", "readWrite"),
                    "datacenter_name": ds_data.get("datacenter_name", ""),
                    "cluster_name": ds_data.get("cluster_name", ""),
                    "capacity_gb": ds_data.get("capacity_gb", 0),
                    "free_gb": ds_data.get("free_gb", 0),
                    "uncommitted_gb": ds_data.get("uncommitted_gb", 0),
                    "vm_count": ds_data.get("vm_count", 0),
                    "usage_percent": ds_data.get("usage_percent", 0.0),
                    "nfs_server": ds_data.get("nfs_server", ""),
                    "nfs_path": ds_data.get("nfs_path", ""),
                    "is_accessible": ds_data.get("is_accessible", True),
                    "is_maintenance": ds_data.get("is_maintenance", False),
                    "multiple_host_access": ds_data.get("multiple_host_access", True),
                    "is_active": True,
                    "last_sync_time": timezone.now(),
                },
            )

            # 更新关联的主机
            if ds_data.get("host_names"):
                hosts = Host.objects.filter(platform=platform, name__in=ds_data["host_names"])
                datastore.hosts.set(hosts)

            action = "创建" if created else "更新"
            logger.debug(f"{action}数据存储: {datastore.name}")

            return datastore

    except Exception as e:
        logger.error(f"同步数据存储到数据库失败 {ds_data['name']}: {str(e)}")
        raise


def sync_template_to_db(platform: Platform, template_data: Dict[str, Any]) -> VMTemplate:
    """
    同步模板信息到数据库

    Args:
        platform: 平台对象
        template_data: 模板数据

    Returns:
        模板对象
    """
    try:
        with transaction.atomic():
            # 根据 UUID 查找或创建模板
            template, created = VMTemplate.objects.update_or_create(
                platform=platform,
                uuid=template_data["uuid"],
                defaults={
                    "name": template_data["name"],
                    "display_name": template_data.get("display_name", ""),
                    "mo_ref": template_data.get("mo_ref", ""),
                    "os_type": template_data.get("os_type", ""),
                    "cpu_count": template_data.get("cpu_count", 1),
                    "memory_mb": template_data.get("memory_mb", 1024),
                    "disk_gb": template_data.get("disk_gb", 20),
                    "category": template_data.get("category", ""),
                    "is_active": True,
                },
            )

            action = "创建" if created else "更新"
            logger.debug(f"{action}模板: {template.name}")

            return template

    except Exception as e:
        logger.error(f"同步模板到数据库失败 {template_data['name']}: {str(e)}")
        raise
