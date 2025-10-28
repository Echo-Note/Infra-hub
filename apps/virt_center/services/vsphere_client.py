#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
vSphere 客户端连接管理
支持 vCenter 和 ESXi 连接
"""

import logging
import ssl
from typing import Optional

from pyVim import connect
from pyVmomi import vim

logger = logging.getLogger(__name__)


class VSphereClient:
    """vSphere 客户端封装类"""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        ssl_verify: bool = False,
    ):
        """
        初始化 vSphere 客户端

        Args:
            host: vCenter/ESXi 主机地址
            username: 登录用户名
            password: 登录密码
            port: 连接端口，默认 443
            ssl_verify: 是否验证 SSL 证书
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.ssl_verify = ssl_verify
        self._service_instance: Optional[vim.ServiceInstance] = None
        self._session_manager: Optional[vim.SessionManager] = None

    def connect(self) -> vim.ServiceInstance:
        """
        连接到 vSphere

        Returns:
            vim.ServiceInstance: 服务实例对象

        Raises:
            vim.fault.InvalidLogin: 登录失败
            Exception: 连接失败
        """
        try:
            # 清理主机地址（移除协议前缀）
            host = self.host.replace("https://", "").replace("http://", "").strip("/")

            # 创建 SSL 上下文
            if not self.ssl_verify:
                # 禁用 SSL 验证（适用于自签名证书）
                context = ssl._create_unverified_context()
            else:
                # 启用 SSL 验证
                context = ssl.create_default_context()
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED

            # 连接到 vCenter/ESXi
            logger.info(f"正在连接到 vSphere: {host}:{self.port}")
            self._service_instance = connect.SmartConnect(
                host=host,
                user=self.username,
                pwd=self.password,
                port=self.port,
                sslContext=context,
            )

            if not self._service_instance:
                raise Exception("无法连接到 vSphere")

            # 获取会话管理器
            self._session_manager = self._service_instance.content.sessionManager

            logger.info(f"成功连接到 vSphere: {host}")
            return self._service_instance

        except vim.fault.InvalidLogin as e:
            logger.error(f"vSphere 登录失败: {e.msg}")
            raise
        except ssl.SSLError as e:
            logger.error(f"SSL 连接失败: {str(e)}")
            logger.info("提示：如果使用自签名证书，请设置 ssl_verify=False")
            raise
        except Exception as e:
            logger.error(f"连接 vSphere 失败: {str(e)}")
            raise

    def disconnect(self):
        """断开 vSphere 连接"""
        if self._service_instance:
            try:
                connect.Disconnect(self._service_instance)
                logger.info(f"已断开与 vSphere 的连接: {self.host}")
            except Exception as e:
                logger.warning(f"断开连接时出错: {str(e)}")
            finally:
                self._service_instance = None
                self._session_manager = None

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        if not self._service_instance:
            return False
        try:
            # 尝试获取当前时间来验证连接
            self._service_instance.CurrentTime()
            return True
        except Exception:
            return False

    @property
    def service_instance(self) -> vim.ServiceInstance:
        """获取服务实例（自动连接）"""
        if not self.is_connected:
            self.connect()
        return self._service_instance

    @property
    def content(self) -> vim.ServiceInstanceContent:
        """获取服务内容"""
        return self.service_instance.RetrieveContent()

    def get_about_info(self) -> dict:
        """
        获取 vSphere 版本信息

        Returns:
            dict: 包含 vSphere 版本、构建号等信息
        """
        about = self.content.about
        return {
            "name": about.name,
            "full_name": about.fullName,
            "vendor": about.vendor,
            "version": about.version,
            "build": about.build,
            "api_type": about.apiType,
            "api_version": about.apiVersion,
            "instance_uuid": about.instanceUuid,
        }

    def get_datacenters(self) -> list[vim.Datacenter]:
        """
        获取所有数据中心

        Returns:
            list: 数据中心对象列表
        """
        container = self.content.rootFolder
        viewType = [vim.Datacenter]
        recursive = True
        containerView = self.content.viewManager.CreateContainerView(container, viewType, recursive)
        datacenters = containerView.view
        containerView.Destroy()
        return datacenters

    def get_clusters(self, datacenter: Optional[vim.Datacenter] = None) -> list[vim.ClusterComputeResource]:
        """
        获取集群列表

        Args:
            datacenter: 指定数据中心，为 None 则获取所有

        Returns:
            list: 集群对象列表
        """
        container = datacenter.hostFolder if datacenter else self.content.rootFolder
        viewType = [vim.ClusterComputeResource]
        recursive = True
        containerView = self.content.viewManager.CreateContainerView(container, viewType, recursive)
        clusters = containerView.view
        containerView.Destroy()
        return clusters

    def get_hosts(self, datacenter: Optional[vim.Datacenter] = None) -> list[vim.HostSystem]:
        """
        获取 ESXi 主机列表

        Args:
            datacenter: 指定数据中心，为 None 则获取所有

        Returns:
            list: ESXi 主机对象列表
        """
        container = datacenter.hostFolder if datacenter else self.content.rootFolder
        viewType = [vim.HostSystem]
        recursive = True
        containerView = self.content.viewManager.CreateContainerView(container, viewType, recursive)
        hosts = containerView.view
        containerView.Destroy()
        return hosts

    def get_vms(self, datacenter: Optional[vim.Datacenter] = None) -> list[vim.VirtualMachine]:
        """
        获取虚拟机列表

        Args:
            datacenter: 指定数据中心，为 None 则获取所有

        Returns:
            list: 虚拟机对象列表
        """
        container = datacenter.vmFolder if datacenter else self.content.rootFolder
        viewType = [vim.VirtualMachine]
        recursive = True
        containerView = self.content.viewManager.CreateContainerView(container, viewType, recursive)
        vms = containerView.view
        containerView.Destroy()
        return vms

    def get_datastores(self, datacenter: Optional[vim.Datacenter] = None) -> list[vim.Datastore]:
        """
        获取数据存储列表

        Args:
            datacenter: 指定数据中心，为 None 则获取所有

        Returns:
            list: 数据存储对象列表
        """
        container = datacenter.datastoreFolder if datacenter else self.content.rootFolder
        viewType = [vim.Datastore]
        recursive = True
        containerView = self.content.viewManager.CreateContainerView(container, viewType, recursive)
        datastores = containerView.view
        containerView.Destroy()
        return datastores

    def get_networks(self, datacenter: Optional[vim.Datacenter] = None) -> list:
        """
        获取网络列表

        Args:
            datacenter: 指定数据中心，为 None 则获取所有

        Returns:
            list: 网络对象列表
        """
        container = datacenter.networkFolder if datacenter else self.content.rootFolder
        viewType = [vim.Network]
        recursive = True
        containerView = self.content.viewManager.CreateContainerView(container, viewType, recursive)
        networks = containerView.view
        containerView.Destroy()
        return networks

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


def get_vsphere_client(platform) -> VSphereClient:
    """
    从平台对象创建 vSphere 客户端

    Args:
        platform: Platform 模型实例

    Returns:
        VSphereClient: vSphere 客户端实例

    Example:
        from apps.virt_center.models import Platform
        from apps.virt_center.services import get_vsphere_client

        platform = Platform.objects.get(name="生产环境 vCenter")
        client = get_vsphere_client(platform)

        # 使用上下文管理器自动连接和断开
        with client:
            about = client.get_about_info()
            print(about)

        # 或手动管理连接
        client.connect()
        try:
            vms = client.get_vms()
            for vm in vms:
                print(vm.name)
        finally:
            client.disconnect()
    """
    from apps.common.utils.crypto import decrypt_password

    # 获取认证凭据
    credential = platform.credential
    logger.info(f"获取到平台认证凭据: {credential.username}")
    logger.info(f"获取到平台认证凭据: {credential.password}")

    return VSphereClient(
        host=platform.host,
        username=credential.username,
        password=credential.password,  # 会自动解密
        port=platform.port,
        ssl_verify=platform.ssl_verify,
    )


if __name__ == "__main__":
    # 测试连接示例
    # 注意：
    # 1. host 参数不要包含 https:// 前缀，只需要 IP 或域名
    # 2. 如果使用自签名证书，设置 ssl_verify=False

    import os

    client = VSphereClient(
        host=os.environ.get("vsphere_host"),  # 不要包含 https:// 前缀
        username=os.environ.get("vsphere_username"),  # 修改为你的用户名
        password=os.environ.get("vsphere_password"),  # 修改为你的密码
        port=443,
        ssl_verify=False,  # 自签名证书使用 False
    )

    try:
        with client:
            # 获取 vSphere 版本信息
            about = client.get_about_info()
            print("=" * 60)
            print("vSphere 连接成功！")
            print("=" * 60)
            print(f"名称: {about['name']}")
            print(f"完整名称: {about['full_name']}")
            print(f"版本: {about['version']}")
            print(f"构建号: {about['build']}")
            print(f"API 类型: {about['api_type']}")
            print(f"API 版本: {about['api_version']}")
            print("=" * 60)

            # 获取数据中心列表
            datacenters = client.get_datacenters()
            print(f"\n数据中心数量: {len(datacenters)}")
            for dc in datacenters:
                print(f"  - {dc.name}")

            # 获取主机列表
            hosts = client.get_hosts()
            print(f"\nESXi 主机数量: {len(hosts)}")
            for host in hosts[:5]:  # 只显示前5个
                print(f"  - {host.name}")

            # 获取虚拟机列表
            vms = client.get_vms()
            print(f"\n虚拟机数量: {len(vms)}")
            for vm in vms[:5]:  # 只显示前5个
                status = vm.runtime.powerState
                print(f"  - {vm.name} ({status})")

    except vim.fault.InvalidLogin as e:
        print(f"❌ 登录失败: 用户名或密码错误")
    except ssl.SSLError as e:
        print(f"❌ SSL 错误: {e}")
        print("💡 提示: 如果使用自签名证书，请设置 ssl_verify=False")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n💡 检查清单:")
        print("  1. vCenter/ESXi 地址是否正确（不要包含 https:// 前缀）")
        print("  2. 网络是否可达（可以 ping 或 telnet 测试）")
        print("  3. 用户名密码是否正确")
        print("  4. 端口是否正确（默认 443）")
        print("  5. 如果使用自签名证书，ssl_verify 应设为 False")
