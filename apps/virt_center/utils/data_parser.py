#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
vSphere 数据解析模块
将 vSphere API 返回的对象转换为字典格式
"""

import logging
from typing import Any, Dict, List, Optional

from pyVmomi import vim

logger = logging.getLogger(__name__)


def safe_get_attr(obj, attr: str, default=None):
    """
    安全获取对象属性

    Args:
        obj: 对象
        attr: 属性名
        default: 默认值

    Returns:
        属性值或默认值
    """
    try:
        value = getattr(obj, attr, default)
        return value if value is not None else default
    except Exception:
        return default


def parse_platform_info(
    about_info: Dict,
    datacenters: List[str],
    cluster_count: int,
    host_count: int,
    vm_count: int,
) -> Dict[str, Any]:
    """
    解析平台信息

    Args:
        about_info: vSphere 关于信息
        datacenters: 数据中心列表
        cluster_count: 集群数量
        host_count: 主机数量
        vm_count: 虚拟机数量

    Returns:
        平台信息字典
    """
    return {
        "version": about_info.get("version", ""),
        "build": about_info.get("build", ""),
        "datacenter": datacenters[0] if datacenters else "",
        "total_hosts": host_count,
        "total_vms": vm_count,
        "total_clusters": cluster_count,
        "status": 1,  # 已连接
    }


def parse_host_info(host: vim.HostSystem) -> Dict[str, Any]:
    """
    解析主机信息

    Args:
        host: vSphere 主机对象

    Returns:
        主机信息字典
    """
    try:
        # 基本信息
        name = host.name
        hardware = host.hardware
        runtime = host.runtime
        summary = host.summary
        config = host.config

        # 硬件信息
        hardware_info = summary.hardware if summary else None
        cpu_info = hardware.cpuInfo if hardware else None

        # 网络信息
        network_info = config.network if config else None

        # 状态信息
        connection_state = str(runtime.connectionState) if runtime else "unknown"
        power_state = str(runtime.powerState) if runtime else "unknown"

        # 确定运行状态
        if connection_state == "connected":
            if runtime.inMaintenanceMode:
                status = 2  # 维护中
            else:
                status = 1  # 在线
        elif connection_state == "disconnected":
            status = 0  # 离线
        else:
            status = 5  # 未知

        # 资源使用情况
        quick_stats = summary.quickStats if summary else None

        # 集群信息
        parent = host.parent
        cluster_name = ""
        if parent and isinstance(parent, vim.ClusterComputeResource):
            cluster_name = parent.name

        # 数据中心信息
        datacenter_name = ""
        obj = host.parent
        while obj:
            if isinstance(obj, vim.Datacenter):
                datacenter_name = obj.name
                break
            obj = getattr(obj, "parent", None)

        host_data = {
            # 基本信息
            "name": name,
            "hostname": (
                config.network.dnsConfig.hostName if config and config.network and config.network.dnsConfig else name
            ),
            "ip_address": name,  # 通常 host.name 就是管理 IP
            # vSphere 对象标识
            "mo_ref": str(host._moId),
            "uuid": hardware_info.uuid if hardware_info else "",
            # 集群信息
            "cluster_name": cluster_name,
            "datacenter_name": datacenter_name,
            # 状态信息
            "status": status,
            "power_state": power_state,
            "connection_state": connection_state,
            # 系统信息
            "vendor": hardware_info.vendor if hardware_info else "",
            "model": hardware_info.model if hardware_info else "",
            "esxi_version": config.product.version if config and config.product else "",
            "esxi_build": config.product.build if config and config.product else "",
            # CPU 信息
            "cpu_model": summary.hardware.cpuModel if summary and summary.hardware else "",
            "cpu_cores": cpu_info.numCpuCores if cpu_info else 0,
            "cpu_threads": cpu_info.numCpuThreads if cpu_info else 0,
            "cpu_sockets": hardware_info.numCpuPkgs if hardware_info else 0,
            "cpu_frequency": cpu_info.hz // 1000000 if cpu_info and cpu_info.hz else 0,  # 转换为 MHz
            # 内存信息
            "memory_total": hardware_info.memorySize // (1024 * 1024) if hardware_info else 0,  # 转换为 MB
            # 资源使用统计
            "vm_count": len(host.vm) if host.vm else 0,
            "cpu_usage": (
                quick_stats.overallCpuUsage / (cpu_info.hz / 1000000) * 100
                if quick_stats and quick_stats.overallCpuUsage and cpu_info and cpu_info.hz
                else 0.0
            ),
            "memory_usage": (
                quick_stats.overallMemoryUsage / (hardware_info.memorySize / (1024 * 1024)) * 100
                if quick_stats and quick_stats.overallMemoryUsage and hardware_info and hardware_info.memorySize
                else 0.0
            ),
            # 管理信息
            "in_maintenance": runtime.inMaintenanceMode if runtime else False,
        }

        return host_data

    except Exception as e:
        logger.error(f"解析主机信息失败 {host.name}: {str(e)}")
        raise


def parse_vm_info(vm: vim.VirtualMachine) -> Dict[str, Any]:
    """
    解析虚拟机信息

    Args:
        vm: vSphere 虚拟机对象

    Returns:
        虚拟机信息字典
    """
    try:
        # 基本信息
        name = vm.name
        config = vm.config
        runtime = vm.runtime
        summary = vm.summary
        guest = vm.guest

        # 跳过无效的虚拟机
        if not config:
            logger.warning(f"虚拟机 {name} 缺少配置信息，跳过")
            return None

        # 状态信息
        power_state = str(runtime.powerState) if runtime else "poweredOff"
        connection_state = str(runtime.connectionState) if runtime else ""

        # 确定运行状态
        status_map = {
            "poweredOn": 1,  # 运行中
            "poweredOff": 2,  # 已停止
            "suspended": 3,  # 已挂起
        }
        status = status_map.get(power_state, 0)  # 未知

        # 主机信息
        host_name = runtime.host.name if runtime and runtime.host else ""

        # 集群信息
        cluster_name = ""
        if runtime and runtime.host:
            parent = runtime.host.parent
            if parent and isinstance(parent, vim.ClusterComputeResource):
                cluster_name = parent.name

        # 数据中心信息
        datacenter_name = ""
        obj = vm.parent
        while obj:
            if isinstance(obj, vim.Datacenter):
                datacenter_name = obj.name
                break
            obj = getattr(obj, "parent", None)

        # Guest 操作系统信息
        os_full_name = config.guestFullName if config else ""
        guest_id = config.guestId if config else ""

        # 简单推断操作系统类型
        os_type = "other"
        guest_lower = (guest_id or "").lower()
        if "win" in guest_lower:
            os_type = "windows"
        elif "centos" in guest_lower:
            os_type = "centos"
        elif "ubuntu" in guest_lower:
            os_type = "ubuntu"
        elif "debian" in guest_lower:
            os_type = "debian"
        elif "rhel" in guest_lower or "redhat" in guest_lower:
            os_type = "redhat"
        elif "linux" in guest_lower:
            os_type = "linux"

        # VMware Tools 状态
        tools_status = str(guest.toolsStatus) if guest else ""
        tools_version = str(guest.toolsVersion) if guest else ""
        guest_state = str(guest.guestState) if guest else ""

        # IP 地址
        ip_address = guest.ipAddress if guest and guest.ipAddress else None

        # 网络信息
        mac_address = ""
        if config and config.hardware:
            for device in config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    mac_address = device.macAddress
                    break

        # 磁盘信息
        disk_count = 0
        total_disk_gb = 0
        if config and config.hardware:
            for device in config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    disk_count += 1
                    total_disk_gb += device.capacityInKB // (1024 * 1024)  # 转换为 GB

        # 快照信息
        has_snapshots = vm.snapshot is not None
        snapshot_count = len(vm.snapshot.rootSnapshotList) if vm.snapshot and vm.snapshot.rootSnapshotList else 0

        # 资源使用情况
        quick_stats = summary.quickStats if summary else None

        vm_data = {
            # 基本信息
            "name": name,
            "display_name": config.name if config else name,
            # vSphere 对象标识
            "mo_ref": str(vm._moId),
            "uuid": config.uuid if config else "",
            "instance_uuid": config.instanceUuid if config else "",
            # 位置信息
            "cluster_name": cluster_name,
            "datacenter_name": datacenter_name,
            "resource_pool": str(vm.resourcePool.name) if vm.resourcePool else "",
            "folder": str(vm.parent.name) if vm.parent else "",
            # 状态信息
            "status": status,
            "power_state": power_state,
            "connection_state": connection_state,
            # 操作系统信息
            "os_type": os_type,
            "os_full_name": os_full_name,
            "guest_id": guest_id,
            "guest_state": guest_state,
            "tools_status": tools_status,
            "tools_version": tools_version,
            # 硬件配置
            "cpu_count": config.hardware.numCPU if config and config.hardware else 1,
            "cpu_cores_per_socket": config.hardware.numCoresPerSocket if config and config.hardware else 1,
            "memory_mb": config.hardware.memoryMB if config and config.hardware else 1024,
            # 虚拟硬件版本
            "hardware_version": config.version if config else "",
            # 网络信息
            "ip_address": ip_address,
            "mac_address": mac_address,
            "hostname": guest.hostName if guest and guest.hostName else "",
            # 磁盘信息摘要
            "disk_count": disk_count,
            "total_disk_gb": total_disk_gb,
            # 资源使用（快照值）
            "cpu_usage_percent": (
                quick_stats.overallCpuUsage / (config.hardware.numCPU * 100)  # 假设每个 vCPU 100 MHz
                if quick_stats and quick_stats.overallCpuUsage and config and config.hardware
                else 0.0
            ),
            "memory_usage_percent": (
                quick_stats.guestMemoryUsage / config.hardware.memoryMB * 100
                if quick_stats and quick_stats.guestMemoryUsage and config and config.hardware
                else 0.0
            ),
            # 快照信息
            "has_snapshots": has_snapshots,
            "snapshot_count": snapshot_count,
            # 管理信息
            "is_template": config.template if config else False,
            # 时间信息
            "boot_time": runtime.bootTime if runtime and runtime.bootTime else None,
            # 主机名称（用于关联）
            "host_name": host_name,
        }

        return vm_data

    except Exception as e:
        logger.error(f"解析虚拟机信息失败 {vm.name}: {str(e)}")
        raise


def parse_datastore_info(datastore: vim.Datastore) -> Dict[str, Any]:
    """
    解析数据存储信息

    Args:
        datastore: vSphere 数据存储对象

    Returns:
        数据存储信息字典
    """
    try:
        # 基本信息
        name = datastore.name
        summary = datastore.summary
        info = datastore.info

        # 存储类型
        ds_type = summary.type.lower() if summary and summary.type else "unknown"

        # 映射到模型中的类型
        type_map = {
            "vmfs": "vmfs",
            "nfs": "nfs",
            "nfs41": "nfs41",
            "vsan": "vsan",
            "vvol": "vvol",
        }
        datastore_type = type_map.get(ds_type, "vmfs")

        # 访问模式
        access_mode = "readWrite" if summary and not summary.accessible else "readOnly"

        # 容量信息（字节转 GB）
        capacity_gb = summary.capacity // (1024**3) if summary and summary.capacity else 0
        free_gb = summary.freeSpace // (1024**3) if summary and summary.freeSpace else 0
        uncommitted_gb = summary.uncommitted // (1024**3) if summary and summary.uncommitted else 0

        # 使用率
        used_gb = capacity_gb - free_gb
        usage_percent = (used_gb / capacity_gb * 100) if capacity_gb > 0 else 0

        # 虚拟机数量
        vm_count = len(datastore.vm) if datastore.vm else 0

        # NFS 特定配置
        nfs_server = ""
        nfs_path = ""
        if isinstance(info, vim.host.NasDatastoreInfo):
            nfs_server = info.nas.remoteHost if info.nas else ""
            nfs_path = info.nas.remotePath if info.nas else ""

        # 数据中心信息
        datacenter_name = ""
        obj = datastore.parent
        while obj:
            if isinstance(obj, vim.Datacenter):
                datacenter_name = obj.name
                break
            obj = getattr(obj, "parent", None)

        # 关联的主机
        host_names = []
        if hasattr(datastore, "host") and datastore.host:
            for host_mount in datastore.host:
                if host_mount.key:
                    host_names.append(host_mount.key.name)

        ds_data = {
            # 基本信息
            "name": name,
            "mo_ref": str(datastore._moId),
            "url": summary.url if summary else "",
            # 存储类型和配置
            "datastore_type": datastore_type,
            "access_mode": access_mode,
            # 位置信息
            "datacenter_name": datacenter_name,
            # 容量信息（单位：GB）
            "capacity_gb": capacity_gb,
            "free_gb": free_gb,
            "uncommitted_gb": uncommitted_gb,
            # 使用统计
            "vm_count": vm_count,
            "usage_percent": min(usage_percent, 100),  # 限制最大100%
            # NFS 特定配置
            "nfs_server": nfs_server,
            "nfs_path": nfs_path,
            # 状态和性能
            "is_accessible": summary.accessible if summary else True,
            "is_maintenance": summary.maintenanceMode != "normal" if summary and summary.maintenanceMode else False,
            "multiple_host_access": summary.multipleHostAccess if summary else True,
            # 关联主机名称
            "host_names": host_names,
        }

        return ds_data

    except Exception as e:
        logger.error(f"解析数据存储信息失败 {datastore.name}: {str(e)}")
        raise


def parse_template_info(vm: vim.VirtualMachine) -> Dict[str, Any]:
    """
    解析模板信息

    Args:
        vm: vSphere 虚拟机对象（模板）

    Returns:
        模板信息字典
    """
    try:
        # 基本信息
        name = vm.name
        config = vm.config

        if not config:
            logger.warning(f"模板 {name} 缺少配置信息，跳过")
            return None

        # 操作系统信息
        os_full_name = config.guestFullName if config else ""
        guest_id = config.guestId if config else ""

        # 简单推断操作系统类型
        os_type = ""
        guest_lower = (guest_id or "").lower()
        if "win" in guest_lower:
            os_type = "windows"
        elif "centos" in guest_lower:
            os_type = "centos"
        elif "ubuntu" in guest_lower:
            os_type = "ubuntu"
        elif "debian" in guest_lower:
            os_type = "debian"
        elif "rhel" in guest_lower or "redhat" in guest_lower:
            os_type = "redhat"
        elif "linux" in guest_lower:
            os_type = "linux"
        else:
            os_type = "other"

        # 磁盘大小
        disk_gb = 0
        if config and config.hardware:
            for device in config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    disk_gb += device.capacityInKB // (1024 * 1024)  # 转换为 GB

        template_data = {
            # 基本信息
            "name": name,
            "display_name": config.name if config else name,
            # vSphere 标识
            "mo_ref": str(vm._moId),
            "uuid": config.uuid if config else "",
            # 模板配置
            "os_type": os_type,
            "cpu_count": config.hardware.numCPU if config and config.hardware else 1,
            "memory_mb": config.hardware.memoryMB if config and config.hardware else 1024,
            "disk_gb": disk_gb,
            # 模板描述
            "category": "",  # 可以根据需要从 vm.parent 或 annotations 获取
        }

        return template_data

    except Exception as e:
        logger.error(f"解析模板信息失败 {vm.name}: {str(e)}")
        raise
