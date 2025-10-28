#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
虚拟化中心 Celery 任务
支持手动调度和定时调度
"""

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from celery import group, shared_task
from celery.utils.log import get_task_logger

from apps.common.celery.decorator import after_app_ready_start, register_as_period_task

from .models import DataStore, Host, Platform, VirtualMachine, VMTemplate
from .signal import platform_status_changed, platform_sync_completed, platform_sync_failed
from .utils.data_parser import (
    parse_datastore_info,
    parse_host_info,
    parse_platform_info,
    parse_template_info,
    parse_vm_info,
)
from .utils.sync_data import (
    sync_datastore_to_db,
    sync_host_to_db,
    sync_platform_to_db,
    sync_template_to_db,
    sync_vm_to_db,
)
from .utils.vsphere_client import get_vsphere_client

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

                        # 同步到数据库
                        sync_host_to_db(platform, host_data)
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

                return {
                    "success": True,
                    "platform_id": platform_id,
                    "synced_count": synced_count,
                    "failed_count": failed_count,
                    "sync_time": timezone.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"连接或获取主机信息失败: {str(e)}")
            raise

    except Exception as exc:
        logger.error(f"同步主机信息失败: {str(exc)}")
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

                        # 同步到数据库
                        sync_vm_to_db(platform, vm_data)
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

    try:
        # 检查平台是否存在
        try:
            platform = Platform.objects.get(id=platform_id, is_active=True)
        except Platform.DoesNotExist:
            logger.error(f"平台不存在或未启用: {platform_id}")
            return {"success": False, "error": "平台不存在或未启用"}

        # 并行执行所有同步任务
        job = group(
            sync_platform_info.s(platform_id),
            sync_hosts.s(platform_id),
            sync_vms.s(platform_id),
            sync_datastores.s(platform_id),
            sync_templates.s(platform_id),
        )

        result = job.apply_async()
        results = result.get(timeout=600)  # 10分钟超时

        logger.info(f"平台所有数据同步完成: {platform.name}")

        sync_result = {
            "success": True,
            "platform_id": platform_id,
            "platform_name": platform.name,
            "results": results,
            "sync_time": timezone.now().isoformat(),
        }

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

    # 并行同步所有平台
    jobs = [sync_all_platform_data.s(str(platform.id)) for platform in platforms]
    job = group(jobs)
    result = job.apply_async()

    try:
        results = result.get(timeout=1800)  # 30分钟超时

        success_count = sum(1 for r in results if r.get("success"))
        failed_count = len(results) - success_count

        logger.info(f"所有平台同步完成: 成功={success_count}, 失败={failed_count}")

        return {
            "success": True,
            "total_platforms": len(platforms),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "sync_time": timezone.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"同步所有平台失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }
