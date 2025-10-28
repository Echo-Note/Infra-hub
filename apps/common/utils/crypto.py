#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
加密解密工具模块
用于处理敏感信息（密码、SSH Key、Token等）的加密存储
"""

import base64
import logging

from django.conf import settings

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class CryptoHandler:
    """加密解密处理器"""

    _fernet_instance = None

    @classmethod
    def _get_fernet(cls):
        """获取 Fernet 实例（单例模式）"""
        if cls._fernet_instance is None:
            # 从 Django SECRET_KEY 派生 Fernet 密钥
            secret_key = settings.SECRET_KEY.encode()
            # 使用固定 salt（生产环境建议配置化）
            salt = b"infra-hub-crypto-salt-v1"

            # 使用 PBKDF2HMAC 派生密钥
            kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)  # 32 字节 = 256 位
            key = base64.urlsafe_b64encode(kdf.derive(secret_key))
            cls._fernet_instance = Fernet(key)

        return cls._fernet_instance

    @classmethod
    def encrypt(cls, plaintext: str | bytes) -> str:
        """
        加密字符串或字节数据

        Args:
            plaintext: 明文数据（str 或 bytes）

        Returns:
            str: Base64 编码的加密字符串

        Raises:
            ValueError: 输入数据为空
            Exception: 加密失败
        """
        if not plaintext:
            raise ValueError("加密数据不能为空")

        try:
            # 确保是字节类型
            if isinstance(plaintext, str):
                plaintext = plaintext.encode("utf-8")

            fernet = cls._get_fernet()
            encrypted_data = fernet.encrypt(plaintext)
            # 返回 base64 编码的字符串，方便存储
            return encrypted_data.decode("utf-8")

        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    @classmethod
    def decrypt(cls, ciphertext: str | bytes) -> str:
        """
        解密数据

        Args:
            ciphertext: 加密的数据（str 或 bytes）

        Returns:
            str: 解密后的明文字符串

        Raises:
            ValueError: 输入数据为空
            InvalidToken: 解密失败（数据损坏或密钥错误）
        """
        if not ciphertext:
            raise ValueError("解密数据不能为空")

        try:
            # 确保是字节类型
            if isinstance(ciphertext, str):
                ciphertext = ciphertext.encode("utf-8")

            fernet = cls._get_fernet()
            decrypted_data = fernet.decrypt(ciphertext)
            return decrypted_data.decode("utf-8")

        except InvalidToken:
            logger.error("解密失败：无效的加密数据或密钥不匹配")
            raise
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise

    @classmethod
    def encrypt_dict(cls, data: dict) -> dict:
        """
        加密字典中的敏感字段

        Args:
            data: 包含敏感信息的字典

        Returns:
            dict: 加密后的字典副本
        """
        encrypted_data = data.copy()
        sensitive_fields = ["password", "token", "secret", "ssh_key", "private_key", "api_key"]

        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    encrypted_data[field] = cls.encrypt(encrypted_data[field])
                except Exception as e:
                    logger.warning(f"加密字段 {field} 失败: {e}")

        return encrypted_data

    @classmethod
    def decrypt_dict(cls, data: dict) -> dict:
        """
        解密字典中的敏感字段

        Args:
            data: 包含加密信息的字典

        Returns:
            dict: 解密后的字典副本
        """
        decrypted_data = data.copy()
        sensitive_fields = ["password", "token", "secret", "ssh_key", "private_key", "api_key"]

        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = cls.decrypt(decrypted_data[field])
                except InvalidToken:
                    # 如果解密失败，可能是明文数据，保持原样
                    logger.debug(f"字段 {field} 解密失败，可能是明文数据")
                except Exception as e:
                    logger.warning(f"解密字段 {field} 失败: {e}")

        return decrypted_data


# 便捷函数
def encrypt_password(password: str) -> str:
    """加密密码"""
    return CryptoHandler.encrypt(password)


def decrypt_password(encrypted_password: str) -> str:
    """解密密码"""
    return CryptoHandler.decrypt(encrypted_password)


def encrypt_ssh_key(ssh_key: str) -> str:
    """加密 SSH 私钥"""
    return CryptoHandler.encrypt(ssh_key)


def decrypt_ssh_key(encrypted_ssh_key: str) -> str:
    """解密 SSH 私钥"""
    return CryptoHandler.decrypt(encrypted_ssh_key)


def encrypt_token(token: str) -> str:
    """加密 Token"""
    return CryptoHandler.encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """解密 Token"""
    return CryptoHandler.decrypt(encrypted_token)
