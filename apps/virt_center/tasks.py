#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心 Celery 任务
支持手动调度和定时调度
"""

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from celery import shared_task
from celery.utils.log import get_task_logger

from apps.common.celery.decorator import after_app_ready_start, register_as_period_task

from .models import DataStore, Host, HostMetrics, OperationTask, Platform, VirtualMachine, VMMetrics, VMTemplate
from .services.data_parser import (
    parse_datastore_info,
    parse_host_info,
    parse_host_networks,
    parse_host_resource,
    parse_platform_info,
    parse_template_info,
    parse_vm_disks,
    parse_vm_info,
    parse_vm_networks,
    parse_vm_snapshots,
)
from .services.operation import create_operation_task, update_operation_task_status
from .services.sync_data import (
    sync_datastore_to_db,
    sync_host_networks_to_db,
    sync_host_resource_to_db,
    sync_host_to_db,
    sync_platform_to_db,
    sync_template_to_db,
    sync_vm_disks_to_db,
    sync_vm_networks_to_db,
    sync_vm_snapshots_to_db,
    sync_vm_to_db,
)
from .services.vsphere_client import get_vsphere_client
from .signal import platform_status_changed, platform_sync_completed, platform_sync_failed

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="virt_center.sync_platform_info",
    verbose_name=_("Sync vSphere Platform Info"),
    max_retries=3,
    default_retry_delay=60,
)
def sync_platform_info(self, platform_id: str):
    """
    同步平台信息

    Args:
        platform_id: 平台ID
    """
    try:
        logger.info(f"开始同步平台信息: platform_id={platform_id}")

        # 获取平台对象
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
        except Platform.DoesNotExist:
            logger.error(f"平台不存在或未启用: {platform_id}")
            return {"success": False, "error": "平台不存在或未启用"}

        # 连接 vSphere
        client = get_vsphere_client(platform)

        try:
            with client:
                # 获取平台信息
                about_info = client.get_about_info()
                logger.info(f"获取到平台信息: {about_info.get('full_name')}")

                # 获取数据中心
                datacenters = client.get_datacenters()
                datacenter_names = [dc.name for dc in datacenters]

                # 获取集群
                clusters = client.get_clusters()
                cluster_count = len(clusters)

                # 获取主机
                hosts = client.get_hosts()
                host_count = len(hosts)

                # 获取虚拟机
                vms = client.get_vms()
                vm_count = len(vms)

                # 解析平台信息
                platform_data = parse_platform_info(
                    about_info=about_info,
                    datacenters=datacenter_names,
                    cluster_count=cluster_count,
                    host_count=host_count,
                    vm_count=vm_count,
                )

                # 同步到数据库
                sync_platform_to_db(platform, platform_data)

                logger.info(f"平台信息同步完成: {platform.name}")

                return {
                    "success": True,
                    "platform_id": platform_id,
                    "platform_name": platform.name,
                    "version": platform_data.get("version"),
                    "total_hosts": host_count,
                    "total_vms": vm_count,
                    "sync_time": timezone.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"连接或获取平台信息失败: {str(e)}")
            # 更新平台状态为异常
            old_status = platform.status
            platform.status = Platform.Status.ERROR
            platform.save(update_fields=["status", "updated_time"])

            # 发送状态变化信号
            platform_status_changed.send(
                sender=Platform,
                platform_id=str(platform.id),
                old_status=old_status,
                new_status=platform.status,
            )
            raise

    except Exception as exc:
        logger.error(f"同步平台信息失败: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="virt_center.sync_hosts",
    verbose_name=_("Sync vSphere Hosts"),
    max_retries=3,
    default_retry_delay=60,
)
def sync_hosts(self, platform_id: str):
    """
    同步主机信息

    Args:
        platform_id: 平台ID
    """
    try:
        logger.info(f"开始同步主机信息: platform_id={platform_id}")

        # 获取平台对象
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
        except Platform.DoesNotExist:
            logger.error(f"平台不存在或未启用: {platform_id}")
            return {"success": False, "error": "平台不存在或未启用"}

        # 创建任务记录
        create_operation_task(
            platform=platform,
            task_type="sync_hosts",
            task_name=f"同步平台 {platform.name} 主机信息",
            celery_task_id=self.request.id,
            parameters={"platform_id": platform_id},
        )
        update_operation_task_status(
            celery_task_id=self.request.id,
            status=OperationTask.Status.RUNNING,
        )

        # 连接 vSphere
        client = get_vsphere_client(platform)

        synced_count = 0
        failed_count = 0
        host_uuids = []

        try:
            with client:
                # 获取所有主机
                hosts = client.get_hosts()
                logger.info(f"从 vSphere 获取到 {len(hosts)} 个主机")

                for host in hosts:
                    try:
                        # 解析主机信息
                        host_data = parse_host_info(host)
                        host_uuids.append(host_data["uuid"])

                        # 同步主机基本信息到数据库
                        host_obj = sync_host_to_db(platform, host_data)

                        # 同步主机资源详情
                        resource_data = parse_host_resource(host)
                        sync_host_resource_to_db(host_obj, resource_data)

                        # 同步主机网络配置
                        networks_data = parse_host_networks(host)
                        sync_host_networks_to_db(host_obj, networks_data)

                        synced_count += 1
                        logger.debug(f"同步主机成功: {host_data['name']}")

                    except Exception as e:
                        logger.error(f"同步主机失败 {host.name}: {str(e)}")
                        failed_count += 1
                        continue

                # 标记不再存在的主机
                Host.objects.filter(platform=platform, is_active=True).exclude(uuid__in=host_uuids).update(
                    is_active=False, updated_time=timezone.now()
                )

                logger.info(f"主机同步完成: 成功={synced_count}, 失败={failed_count}")

                result_data = {
                    "success": True,
                    "platform_id": platform_id,
                    "synced_count": synced_count,
                    "failed_count": failed_count,
                    "sync_time": timezone.now().isoformat(),
                }

                # 更新任务状态为成功
                update_operation_task_status(
                    celery_task_id=self.request.id,
                    status=OperationTask.Status.SUCCESS,
                    result=result_data,
                    progress=100,
                )

                return result_data

        except Exception as e:
            logger.error(f"连接或获取主机信息失败: {str(e)}")
            update_operation_task_status(
                celery_task_id=self.request.id,
                status=OperationTask.Status.FAILED,
                error_message=str(e),
            )
            raise

    except Exception as exc:
        logger.error(f"同步主机信息失败: {str(exc)}")
        update_operation_task_status(
            celery_task_id=self.request.id,
            status=OperationTask.Status.FAILED,
            error_message=str(exc),
        )
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="virt_center.sync_vms",
    verbose_name=_("Sync vSphere VMs"),
    max_retries=3,
    default_retry_delay=60,
)
def sync_vms(self, platform_id: str):
    """
    同步虚拟机信息

    Args:
        platform_id: 平台ID
    """
    try:
        logger.info(f"开始同步虚拟机信息: platform_id={platform_id}")

        # 获取平台对象
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
        except Platform.DoesNotExist:
            logger.error(f"平台不存在或未启用: {platform_id}")
            return {"success": False, "error": "平台不存在或未启用"}

        # 连接 vSphere
        client = get_vsphere_client(platform)

        synced_count = 0
        failed_count = 0
        vm_uuids = []

        try:
            with client:
                # 获取所有虚拟机
                vms = client.get_vms()
                logger.info(f"从 vSphere 获取到 {len(vms)} 个虚拟机")

                for vm in vms:
                    try:
                        # 解析虚拟机信息
                        vm_data = parse_vm_info(vm)

                        # 跳过模板（模板在单独的任务中同步）
                        if vm_data.get("is_template"):
                            continue

                        vm_uuids.append(vm_data["uuid"])

                        # 同步虚拟机基本信息到数据库
                        vm_obj = sync_vm_to_db(platform, vm_data)

                        # 同步虚拟机磁盘信息
                        disks_data = parse_vm_disks(vm)
                        sync_vm_disks_to_db(vm_obj, disks_data)

                        # 同步虚拟机网络信息
                        networks_data = parse_vm_networks(vm)
                        sync_vm_networks_to_db(vm_obj, networks_data)

                        # 同步虚拟机快照信息
                        snapshots_data = parse_vm_snapshots(vm)
                        sync_vm_snapshots_to_db(vm_obj, snapshots_data)

                        synced_count += 1
                        logger.debug(f"同步虚拟机成功: {vm_data['name']}")

                    except Exception as e:
                        logger.error(f"同步虚拟机失败 {vm.name}: {str(e)}")
                        failed_count += 1
                        continue

                # 标记不再存在的虚拟机
                VirtualMachine.objects.filter(platform=platform, is_active=True, is_template=False).exclude(
                    uuid__in=vm_uuids
                ).update(is_active=False, updated_time=timezone.now())

                logger.info(f"虚拟机同步完成: 成功={synced_count}, 失败={failed_count}")

                return {
                    "success": True,
                    "platform_id": platform_id,
                    "synced_count": synced_count,
                    "failed_count": failed_count,
                    "sync_time": timezone.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"连接或获取虚拟机信息失败: {str(e)}")
            raise

    except Exception as exc:
        logger.error(f"同步虚拟机信息失败: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="virt_center.sync_datastores",
    verbose_name=_("Sync vSphere Datastores"),
    max_retries=3,
    default_retry_delay=60,
)
def sync_datastores(self, platform_id: str):
    """
    同步数据存储信息

    Args:
        platform_id: 平台ID
    """
    try:
        logger.info(f"开始同步数据存储信息: platform_id={platform_id}")

        # 获取平台对象
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
        except Platform.DoesNotExist:
            logger.error(f"平台不存在或未启用: {platform_id}")
            return {"success": False, "error": "平台不存在或未启用"}

        # 连接 vSphere
        client = get_vsphere_client(platform)

        synced_count = 0
        failed_count = 0
        datastore_names = []

        try:
            with client:
                # 获取所有数据存储
                datastores = client.get_datastores()
                logger.info(f"从 vSphere 获取到 {len(datastores)} 个数据存储")

                for datastore in datastores:
                    try:
                        # 解析数据存储信息
                        ds_data = parse_datastore_info(datastore)
                        datastore_names.append(ds_data["name"])

                        # 同步到数据库
                        sync_datastore_to_db(platform, ds_data)
                        synced_count += 1

                        logger.debug(f"同步数据存储成功: {ds_data['name']}")

                    except Exception as e:
                        logger.error(f"同步数据存储失败 {datastore.name}: {str(e)}")
                        failed_count += 1
                        continue

                # 标记不再存在的数据存储
                DataStore.objects.filter(platform=platform, is_active=True).exclude(name__in=datastore_names).update(
                    is_active=False, updated_time=timezone.now()
                )

                logger.info(f"数据存储同步完成: 成功={synced_count}, 失败={failed_count}")

                return {
                    "success": True,
                    "platform_id": platform_id,
                    "synced_count": synced_count,
                    "failed_count": failed_count,
                    "sync_time": timezone.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"连接或获取数据存储信息失败: {str(e)}")
            raise

    except Exception as exc:
        logger.error(f"同步数据存储信息失败: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="virt_center.sync_templates",
    verbose_name=_("Sync vSphere VM Templates"),
    max_retries=3,
    default_retry_delay=60,
)
def sync_templates(self, platform_id: str):
    """
    同步虚拟机模板信息

    Args:
        platform_id: 平台ID
    """
    try:
        logger.info(f"开始同步模板信息: platform_id={platform_id}")

        # 获取平台对象
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
        except Platform.DoesNotExist:
            logger.error(f"平台不存在或未启用: {platform_id}")
            return {"success": False, "error": "平台不存在或未启用"}

        # 连接 vSphere
        client = get_vsphere_client(platform)

        synced_count = 0
        failed_count = 0
        template_uuids = []

        try:
            with client:
                # 获取所有虚拟机（包括模板）
                vms = client.get_vms()
                logger.info(f"从 vSphere 获取虚拟机列表，查找模板...")

                for vm in vms:
                    try:
                        # 检查是否为模板
                        if not vm.config or not vm.config.template:
                            continue

                        # 解析模板信息
                        template_data = parse_template_info(vm)
                        template_uuids.append(template_data["uuid"])

                        # 同步到数据库
                        sync_template_to_db(platform, template_data)
                        synced_count += 1

                        logger.debug(f"同步模板成功: {template_data['name']}")

                    except Exception as e:
                        logger.error(f"同步模板失败 {vm.name}: {str(e)}")
                        failed_count += 1
                        continue

                # 标记不再存在的模板
                VMTemplate.objects.filter(platform=platform, is_active=True).exclude(uuid__in=template_uuids).update(
                    is_active=False, updated_time=timezone.now()
                )

                logger.info(f"模板同步完成: 成功={synced_count}, 失败={failed_count}")

                return {
                    "success": True,
                    "platform_id": platform_id,
                    "synced_count": synced_count,
                    "failed_count": failed_count,
                    "sync_time": timezone.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"连接或获取模板信息失败: {str(e)}")
            raise

    except Exception as exc:
        logger.error(f"同步模板信息失败: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="virt_center.sync_all_platform_data",
    verbose_name=_("Sync All Platform Data"),
)
def sync_all_platform_data(self, platform_id: str):
    """
    同步平台所有数据（平台信息、主机、虚拟机、存储、模板）

    Args:
        platform_id: 平台ID

    Returns:
        dict: 同步结果
    """
    logger.info(f"开始同步平台所有数据: platform_id={platform_id}")

    # 创建任务记录
    operation_task = None

    try:
        # 检查平台是否存在
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
        except Platform.DoesNotExist:
            logger.error(f"平台不存在或未启用: {platform_id}")
            return {"success": False, "error": "平台不存在或未启用"}

        # 创建操作任务记录
        operation_task = create_operation_task(
            platform=platform,
            task_type="sync_platform",
            task_name=f"同步平台 {platform.name} 所有数据",
            celery_task_id=self.request.id,
            parameters={"platform_id": platform_id},
        )

        # 更新任务状态为运行中
        update_operation_task_status(
            celery_task_id=self.request.id,
            status=OperationTask.Status.RUNNING,
            current_step="开始同步",
        )

        # 顺序执行所有同步任务（避免在任务内调用 .get()）
        results = []

        # 同步平台信息
        try:
            result = sync_platform_info(platform_id)
            results.append({"task": "sync_platform_info", "result": result})
        except Exception as e:
            logger.error(f"同步平台信息失败: {str(e)}")
            results.append({"task": "sync_platform_info", "error": str(e)})

        # 同步主机
        try:
            result = sync_hosts(platform_id)
            results.append({"task": "sync_hosts", "result": result})
        except Exception as e:
            logger.error(f"同步主机失败: {str(e)}")
            results.append({"task": "sync_hosts", "error": str(e)})

        # 同步虚拟机
        try:
            result = sync_vms(platform_id)
            results.append({"task": "sync_vms", "result": result})
        except Exception as e:
            logger.error(f"同步虚拟机失败: {str(e)}")
            results.append({"task": "sync_vms", "error": str(e)})

        # 同步数据存储
        try:
            result = sync_datastores(platform_id)
            results.append({"task": "sync_datastores", "result": result})
        except Exception as e:
            logger.error(f"同步数据存储失败: {str(e)}")
            results.append({"task": "sync_datastores", "error": str(e)})

        # 同步模板
        try:
            result = sync_templates(platform_id)
            results.append({"task": "sync_templates", "result": result})
        except Exception as e:
            logger.error(f"同步模板失败: {str(e)}")
            results.append({"task": "sync_templates", "error": str(e)})

        logger.info(f"平台所有数据同步完成: {platform.name}")

        sync_result = {
            "success": True,
            "platform_id": platform_id,
            "platform_name": platform.name,
            "results": results,
            "sync_time": timezone.now().isoformat(),
        }

        # 更新任务状态为成功
        update_operation_task_status(
            celery_task_id=self.request.id,
            status=OperationTask.Status.SUCCESS,
            result=sync_result,
            progress=100,
            current_step="同步完成",
        )

        # 发送同步完成信号
        platform_sync_completed.send(
            sender=Platform,
            platform_id=platform_id,
            platform_name=platform.name,
            sync_result=sync_result,
        )

        return sync_result

    except Exception as exc:
        logger.error(f"同步平台所有数据失败: {str(exc)}")

        error_result = {
            "success": False,
            "platform_id": platform_id,
            "error": str(exc),
        }

        # 更新任务状态为失败
        update_operation_task_status(
            celery_task_id=self.request.id,
            status=OperationTask.Status.FAILED,
            error_message=str(exc),
        )

        # 发送同步失败信号
        try:
            platform = Platform.objects.get(id=platform_id)
            platform_sync_failed.send(
                sender=Platform,
                platform_id=platform_id,
                platform_name=platform.name,
                error=str(exc),
            )
        except Exception:
            pass

        return error_result


@shared_task(verbose_name=_("同步所有平台数据"))
@register_as_period_task(interval=3600)
@after_app_ready_start
def sync_all_platforms():
    """定期同步所有启用的平台数据"""
    logger.info("开始定期同步所有平台数据")

    platforms = Platform.objects.filter(is_active=True)

    if not platforms.exists():
        logger.warning("没有启用的平台需要同步")
        return {"success": True, "message": "没有启用的平台"}

    logger.info(f"找到 {platforms.count()} 个启用的平台")

    # 异步启动所有平台的同步任务（不等待结果）
    task_ids = []
    for platform in platforms:
        result = sync_all_platform_data.apply_async(args=[str(platform.id)])
        task_ids.append(
            {
                "platform_id": str(platform.id),
                "platform_name": platform.name,
                "task_id": result.id,
            }
        )

    logger.info(f"已为 {len(task_ids)} 个平台启动同步任务")

    return {
        "success": True,
        "total_platforms": len(platforms),
        "tasks": task_ids,
        "message": "所有平台同步任务已启动",
        "sync_time": timezone.now().isoformat(),
    }


@shared_task(
    bind=True,
    name="virt_center.collect_metrics",
    verbose_name=_("Collect vSphere Metrics"),
    max_retries=3,
    default_retry_delay=60,
)
def collect_metrics(self, platform_id: str):
    """
    采集监控指标（主机和虚拟机）

    Args:
        platform_id: 平台ID
    """
    try:
        logger.info(f"开始采集监控指标: platform_id={platform_id}")

        # 获取平台对象
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
        except Platform.DoesNotExist:
            logger.error(f"平台不存在或未启用: {platform_id}")
            return {"success": False, "error": "平台不存在或未启用"}

        # 连接 vSphere
        client = get_vsphere_client(platform)

        host_metrics_count = 0
        vm_metrics_count = 0
        current_time = timezone.now()

        try:
            with client:
                # 采集主机监控指标
                hosts = client.get_hosts()
                for host_vim in hosts:
                    try:
                        # 查找数据库中的主机
                        host_obj = Host.objects.filter(platform=platform, name=host_vim.name).first()
                        if not host_obj:
                            continue

                        summary = host_vim.summary
                        quick_stats = summary.quickStats if summary else None

                        if quick_stats:
                            HostMetrics.objects.create(
                                host=host_obj,
                                cpu_usage_percent=host_obj.cpu_usage,
                                cpu_usage_mhz=quick_stats.overallCpuUsage or 0,
                                memory_usage_percent=host_obj.memory_usage,
                                memory_used_mb=quick_stats.overallMemoryUsage or 0,
                                collected_at=current_time,
                            )
                            host_metrics_count += 1

                    except Exception as e:
                        logger.error(f"采集主机监控指标失败 {host_vim.name}: {str(e)}")
                        continue

                # 采集虚拟机监控指标
                vms = client.get_vms()
                for vm_vim in vms:
                    try:
                        # 跳过模板
                        if vm_vim.config and vm_vim.config.template:
                            continue

                        # 查找数据库中的虚拟机
                        vm_obj = VirtualMachine.objects.filter(platform=platform, name=vm_vim.name).first()
                        if not vm_obj:
                            continue

                        summary = vm_vim.summary
                        quick_stats = summary.quickStats if summary else None

                        if quick_stats:
                            VMMetrics.objects.create(
                                vm=vm_obj,
                                cpu_usage_percent=vm_obj.cpu_usage_percent,
                                memory_usage_percent=vm_obj.memory_usage_percent,
                                memory_used_mb=quick_stats.guestMemoryUsage or 0,
                                collected_at=current_time,
                            )
                            vm_metrics_count += 1

                    except Exception as e:
                        logger.error(f"采集虚拟机监控指标失败 {vm_vim.name}: {str(e)}")
                        continue

                logger.info(f"监控指标采集完成: 主机={host_metrics_count}, 虚拟机={vm_metrics_count}")

                return {
                    "success": True,
                    "platform_id": platform_id,
                    "host_metrics_count": host_metrics_count,
                    "vm_metrics_count": vm_metrics_count,
                    "collected_at": current_time.isoformat(),
                }

        except Exception as e:
            logger.error(f"连接或采集监控指标失败: {str(e)}")
            raise

    except Exception as exc:
        logger.error(f"采集监控指标失败: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(name="virt_center.collect_all_platforms_metrics")
@register_as_period_task(interval=300)  # 每5分钟采集一次监控指标
def collect_all_platforms_metrics():
    """定期采集所有平台的监控指标"""
    logger.info("开始定期采集所有平台监控指标")

    platforms = Platform.objects.filter(is_active=True)

    if not platforms.exists():
        logger.warning("没有启用的平台需要采集")
        return {"success": True, "message": "没有启用的平台"}

    logger.info(f"找到 {platforms.count()} 个启用的平台")

    # 异步启动所有平台的监控采集任务（不等待结果）
    task_ids = []
    for platform in platforms:
        result = collect_metrics.apply_async(args=[str(platform.id)])
        task_ids.append(
            {
                "platform_id": str(platform.id),
                "platform_name": platform.name,
                "task_id": result.id,
            }
        )

    logger.info(f"已为 {len(task_ids)} 个平台启动监控采集任务")

    return {
        "success": True,
        "total_platforms": len(platforms),
        "tasks": task_ids,
        "message": "所有平台监控采集任务已启动",
    }
