#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
操作日志和任务记录工具
"""

import logging
from datetime import datetime
from typing import Optional

from django.utils import timezone

from apps.virt_center.models import OperationLog, OperationTask, Platform

logger = logging.getLogger(__name__)


def create_operation_task(
    platform: Platform,
    task_type: str,
    task_name: str,
    celery_task_id: str,
    parameters: dict = None,
    creator=None,
) -> OperationTask:
    """
    创建操作任务记录

    Args:
        platform: 平台对象
        task_type: 任务类型
        task_name: 任务名称
        celery_task_id: Celery 任务ID
        parameters: 任务参数
        creator: 创建者

    Returns:
        OperationTask 对象
    """
    try:
        task = OperationTask.objects.create(
            platform=platform,
            task_type=task_type,
            task_name=task_name,
            celery_task_id=celery_task_id,
            status=OperationTask.Status.PENDING,
            parameters=parameters or {},
            scheduled_time=timezone.now(),
            creator=creator,
        )
        logger.debug(f"创建操作任务记录: {task_name}")
        return task
    except Exception as e:
        logger.error(f"创建操作任务记录失败: {str(e)}")
        raise


def update_operation_task_status(
    celery_task_id: str,
    status: int,
    result: dict = None,
    error_message: str = None,
    progress: int = None,
    current_step: str = None,
):
    """
    更新操作任务状态

    Args:
        celery_task_id: Celery 任务ID
        status: 任务状态
        result: 执行结果
        error_message: 错误信息
        progress: 进度
        current_step: 当前步骤
    """
    try:
        task = OperationTask.objects.filter(celery_task_id=celery_task_id).first()
        if not task:
            logger.warning(f"未找到任务记录: {celery_task_id}")
            return

        # 更新字段
        update_fields = ["status", "updated_time"]
        task.status = status

        if result is not None:
            task.result = result
            update_fields.append("result")

        if error_message is not None:
            task.error_message = error_message
            update_fields.append("error_message")

        if progress is not None:
            task.progress = progress
            update_fields.append("progress")

        if current_step is not None:
            task.current_step = current_step
            update_fields.append("current_step")

        # 状态为运行中时设置开始时间
        if status == OperationTask.Status.RUNNING and not task.start_time:
            task.start_time = timezone.now()
            update_fields.append("start_time")

        # 状态为完成或失败时设置结束时间和执行时长
        if status in [OperationTask.Status.SUCCESS, OperationTask.Status.FAILED]:
            task.end_time = timezone.now()
            update_fields.extend(["end_time", "duration_seconds"])

            if task.start_time:
                duration = task.end_time - task.start_time
                task.duration_seconds = int(duration.total_seconds())

        task.save(update_fields=update_fields)
        logger.debug(f"更新任务状态: {celery_task_id} -> {task.get_status_display()}")

    except Exception as e:
        logger.error(f"更新操作任务状态失败: {str(e)}")


def create_operation_log(
    platform: Optional[Platform],
    operator,
    operation_type: str,
    target_type: str,
    target_id: str,
    target_name: str,
    parameters: dict = None,
) -> OperationLog:
    """
    创建操作日志

    Args:
        platform: 平台对象
        operator: 操作人
        operation_type: 操作类型
        target_type: 目标类型
        target_id: 目标ID
        target_name: 目标名称
        parameters: 操作参数

    Returns:
        OperationLog 对象
    """
    try:
        log = OperationLog.objects.create(
            platform=platform,
            operator=operator,
            operation_type=operation_type,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            status=OperationLog.Status.PENDING,
            parameters=parameters or {},
        )
        logger.debug(f"创建操作日志: {operation_type} - {target_name}")
        return log
    except Exception as e:
        logger.error(f"创建操作日志失败: {str(e)}")
        raise


def update_operation_log_status(
    log: OperationLog,
    status: int,
    result: str = None,
    error_message: str = None,
):
    """
    更新操作日志状态

    Args:
        log: 操作日志对象
        status: 状态
        result: 执行结果
        error_message: 错误信息
    """
    try:
        log.status = status

        if result is not None:
            log.result = result

        if error_message is not None:
            log.error_message = error_message

        if status in [OperationLog.Status.SUCCESS, OperationLog.Status.FAILED]:
            log.end_time = timezone.now()
            if log.start_time:
                duration = log.end_time - log.start_time
                log.duration_seconds = int(duration.total_seconds())

        log.save()
        logger.debug(f"更新操作日志状态: {log.operation_type} -> {log.get_status_display()}")

    except Exception as e:
        logger.error(f"更新操作日志状态失败: {str(e)}")
