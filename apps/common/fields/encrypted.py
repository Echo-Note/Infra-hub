#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
加密字段
自动处理数据的加密和解密
"""

from django.db import models

from apps.common.utils.crypto import CryptoHandler


class EncryptedCharField(models.CharField):
    """加密的字符字段"""

    description = "加密存储的字符字段"

    def __init__(self, *args, **kwargs):
        # 加密后的数据会更长，自动调整最大长度
        if "max_length" in kwargs:
            kwargs["max_length"] = kwargs["max_length"] * 2
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        """从数据库读取时自动解密"""
        if value is None:
            return value
        try:
            return CryptoHandler.decrypt(value)
        except Exception:
            # 解密失败时返回原值（可能是明文数据）
            return value

    def get_prep_value(self, value):
        """保存到数据库前自动加密"""
        if value is None:
            return value
        try:
            # 如果已经是加密数据，先解密再重新加密（避免重复加密）
            try:
                CryptoHandler.decrypt(value)
                return value  # 已加密，直接返回
            except Exception:
                # 不是加密数据，进行加密
                return CryptoHandler.encrypt(value)
        except Exception:
            return value


class EncryptedTextField(models.TextField):
    """加密的文本字段（用于 SSH Key 等长文本）"""

    description = "加密存储的文本字段"

    def from_db_value(self, value, expression, connection):
        """从数据库读取时自动解密"""
        if value is None:
            return value
        try:
            return CryptoHandler.decrypt(value)
        except Exception:
            # 解密失败时返回原值
            return value

    def get_prep_value(self, value):
        """保存到数据库前自动加密"""
        if value is None:
            return value
        try:
            # 如果已经是加密数据，先解密再重新加密
            try:
                CryptoHandler.decrypt(value)
                return value  # 已加密，直接返回
            except Exception:
                # 不是加密数据，进行加密
                return CryptoHandler.encrypt(value)
        except Exception:
            return value
