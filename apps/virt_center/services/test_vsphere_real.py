#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
vSphere 客户端真实环境测试
直接连接真实 vSphere 环境，不使用 Mock
"""

import argparse
import os
import sys
import time
from typing import Optional

from pyVmomi import vim
from vsphere_client import VSphereClient


class VSphereRealTest:
    """vSphere 真实环境测试"""

    def __init__(self, host: str, username: str, password: str, port: int = 443, ssl_verify: bool = False):
        """
        初始化测试

        Args:
            host: vCenter/ESXi 地址
            username: 用户名
            password: 密码
            port: 端口
            ssl_verify: 是否验证 SSL 证书
        """
        self.client = VSphereClient(
            host=host,
            username=username,
            password=password,
            port=port,
            ssl_verify=ssl_verify,
        )
        self.test_results = []

    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'=' * 80}")
        print(f" {title}")
        print(f"{'=' * 80}")

    def print_section(self, title: str):
        """打印分节"""
        print(f"\n▶ {title}")
        print("-" * 80)

    def test_connection(self) -> bool:
        """测试1: 连接测试"""
        self.print_section("测试1: 连接到 vSphere")

        try:
            start_time = time.time()
            self.client.connect()
            connection_time = time.time() - start_time

            if self.client.is_connected:
                print(f"✅ 连接成功")
                print(f"   耗时: {connection_time:.2f} 秒")
                self.test_results.append(("连接测试", True, f"{connection_time:.2f}s"))
                return True
            else:
                print(f"❌ 连接失败: 连接状态异常")
                self.test_results.append(("连接测试", False, "连接状态异常"))
                return False

        except Exception as e:
            print(f"❌ 连接失败: {e}")
            self.test_results.append(("连接测试", False, str(e)))
            return False

    def test_about_info(self) -> bool:
        """测试2: 获取版本信息"""
        self.print_section("测试2: 获取 vSphere 版本信息")

        try:
            about = self.client.get_about_info()

            print(f"✅ 成功获取版本信息:")
            print(f"   名称:      {about['name']}")
            print(f"   完整名称:  {about['full_name']}")
            print(f"   供应商:    {about['vendor']}")
            print(f"   版本:      {about['version']}")
            print(f"   构建号:    {about['build']}")
            print(f"   API类型:   {about['api_type']}")
            print(f"   API版本:   {about['api_version']}")
            print(f"   实例UUID:  {about['instance_uuid']}")

            self.test_results.append(("版本信息", True, about["version"]))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("版本信息", False, str(e)))
            return False

    def test_datacenters(self) -> bool:
        """测试3: 获取数据中心"""
        self.print_section("测试3: 获取数据中心列表")

        try:
            start_time = time.time()
            datacenters = self.client.get_datacenters()
            query_time = time.time() - start_time

            print(f"✅ 成功获取 {len(datacenters)} 个数据中心 (耗时: {query_time:.2f}s):")

            for i, dc in enumerate(datacenters, 1):
                print(f"   {i}. {dc.name}")

            self.test_results.append(("数据中心", True, f"{len(datacenters)} 个"))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("数据中心", False, str(e)))
            return False

    def test_clusters(self) -> bool:
        """测试4: 获取集群"""
        self.print_section("测试4: 获取集群列表")

        try:
            start_time = time.time()
            clusters = self.client.get_clusters()
            query_time = time.time() - start_time

            print(f"✅ 成功获取 {len(clusters)} 个集群 (耗时: {query_time:.2f}s):")

            for i, cluster in enumerate(clusters[:20], 1):  # 最多显示20个
                # 获取集群摘要信息
                total_cpu = cluster.summary.numCpuCores if hasattr(cluster.summary, "numCpuCores") else 0
                total_hosts = cluster.summary.numHosts if hasattr(cluster.summary, "numHosts") else 0
                print(f"   {i}. {cluster.name} (主机: {total_hosts}, CPU核心: {total_cpu})")

            if len(clusters) > 20:
                print(f"   ... 还有 {len(clusters) - 20} 个集群未显示")

            self.test_results.append(("集群", True, f"{len(clusters)} 个"))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("集群", False, str(e)))
            return False

    def test_hosts(self) -> bool:
        """测试5: 获取 ESXi 主机"""
        self.print_section("测试5: 获取 ESXi 主机列表")

        try:
            start_time = time.time()
            hosts = self.client.get_hosts()
            query_time = time.time() - start_time

            print(f"✅ 成功获取 {len(hosts)} 个 ESXi 主机 (耗时: {query_time:.2f}s):")

            for i, host in enumerate(hosts[:20], 1):  # 最多显示20个
                # 获取主机详细信息
                try:
                    hw = host.hardware
                    cpu_cores = hw.cpuInfo.numCpuCores
                    memory_gb = hw.memorySize / (1024**3)
                    connection_state = host.runtime.connectionState
                    power_state = host.runtime.powerState

                    print(f"   {i}. {host.name}")
                    print(f"      - CPU: {cpu_cores} 核")
                    print(f"      - 内存: {memory_gb:.1f} GB")
                    print(f"      - 连接状态: {connection_state}")
                    print(f"      - 电源状态: {power_state}")
                except Exception as e:
                    print(f"   {i}. {host.name} (详情获取失败: {e})")

            if len(hosts) > 20:
                print(f"   ... 还有 {len(hosts) - 20} 个主机未显示")

            self.test_results.append(("ESXi主机", True, f"{len(hosts)} 个"))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("ESXi主机", False, str(e)))
            return False

    def test_vms(self) -> bool:
        """测试6: 获取虚拟机"""
        self.print_section("测试6: 获取虚拟机列表")

        try:
            start_time = time.time()
            vms = self.client.get_vms()
            query_time = time.time() - start_time

            print(f"✅ 成功获取 {len(vms)} 个虚拟机 (耗时: {query_time:.2f}s):")

            # 统计状态
            power_on = sum(1 for vm in vms if vm.runtime.powerState == "poweredOn")
            power_off = sum(1 for vm in vms if vm.runtime.powerState == "poweredOff")
            suspended = sum(1 for vm in vms if vm.runtime.powerState == "suspended")

            print(f"\n   状态统计:")
            print(f"   - 运行中: {power_on}")
            print(f"   - 已关机: {power_off}")
            print(f"   - 已挂起: {suspended}")

            print(f"\n   虚拟机详情 (前20个):")
            for i, vm in enumerate(vms[:20], 1):
                try:
                    power_state = vm.runtime.powerState
                    cpu = vm.config.hardware.numCPU if vm.config else 0
                    memory_mb = vm.config.hardware.memoryMB if vm.config else 0
                    guest_os = vm.config.guestFullName if vm.config else "Unknown"

                    # 图标表示状态
                    status_icon = "🟢" if power_state == "poweredOn" else "🔴" if power_state == "poweredOff" else "🟡"

                    print(f"   {i}. {status_icon} {vm.name}")
                    print(f"      - CPU: {cpu} vCPU, 内存: {memory_mb} MB")
                    print(f"      - 操作系统: {guest_os}")
                    print(f"      - 状态: {power_state}")
                except Exception as e:
                    print(f"   {i}. {vm.name} (详情获取失败)")

            if len(vms) > 20:
                print(f"   ... 还有 {len(vms) - 20} 个虚拟机未显示")

            self.test_results.append(("虚拟机", True, f"{len(vms)} 个"))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("虚拟机", False, str(e)))
            return False

    def test_datastores(self) -> bool:
        """测试7: 获取数据存储"""
        self.print_section("测试7: 获取数据存储列表")

        try:
            start_time = time.time()
            datastores = self.client.get_datastores()
            query_time = time.time() - start_time

            print(f"✅ 成功获取 {len(datastores)} 个数据存储 (耗时: {query_time:.2f}s):")

            # 计算总容量
            total_capacity = 0
            total_free = 0

            for i, ds in enumerate(datastores[:20], 1):
                try:
                    capacity_gb = ds.summary.capacity / (1024**3)
                    free_gb = ds.summary.freeSpace / (1024**3)
                    used_gb = capacity_gb - free_gb
                    used_percent = (used_gb / capacity_gb * 100) if capacity_gb > 0 else 0
                    ds_type = ds.summary.type
                    accessible = "✅" if ds.summary.accessible else "❌"

                    total_capacity += capacity_gb
                    total_free += free_gb

                    print(f"   {i}. {ds.name} ({ds_type}) {accessible}")
                    print(f"      - 容量: {capacity_gb:.1f} GB")
                    print(f"      - 已用: {used_gb:.1f} GB ({used_percent:.1f}%)")
                    print(f"      - 可用: {free_gb:.1f} GB")
                except Exception as e:
                    print(f"   {i}. {ds.name} (详情获取失败)")

            if len(datastores) > 20:
                print(f"   ... 还有 {len(datastores) - 20} 个数据存储未显示")

            print(f"\n   总容量统计:")
            print(f"   - 总容量: {total_capacity:.1f} GB")
            print(f"   - 已用: {total_capacity - total_free:.1f} GB")
            print(f"   - 可用: {total_free:.1f} GB")

            self.test_results.append(("数据存储", True, f"{len(datastores)} 个"))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("数据存储", False, str(e)))
            return False

    def test_networks(self) -> bool:
        """测试8: 获取网络"""
        self.print_section("测试8: 获取网络列表")

        try:
            start_time = time.time()
            networks = self.client.get_networks()
            query_time = time.time() - start_time

            print(f"✅ 成功获取 {len(networks)} 个网络 (耗时: {query_time:.2f}s):")

            for i, network in enumerate(networks[:20], 1):
                print(f"   {i}. {network.name}")

            if len(networks) > 20:
                print(f"   ... 还有 {len(networks) - 20} 个网络未显示")

            self.test_results.append(("网络", True, f"{len(networks)} 个"))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("网络", False, str(e)))
            return False

    def test_vm_details(self, vm_name: Optional[str] = None) -> bool:
        """测试9: 获取虚拟机详细信息"""
        self.print_section("测试9: 获取虚拟机详细信息")

        try:
            vms = self.client.get_vms()

            if not vms:
                print("⚠️ 没有找到虚拟机")
                return True

            # 选择一个虚拟机
            if vm_name:
                target_vm = next((vm for vm in vms if vm.name == vm_name), None)
                if not target_vm:
                    print(f"⚠️ 未找到虚拟机: {vm_name}")
                    target_vm = vms[0]
            else:
                target_vm = vms[0]

            print(f"\n虚拟机: {target_vm.name}")
            print(f"{'-' * 80}")

            # 基本信息
            print(f"\n📌 基本信息:")
            print(f"   UUID: {target_vm.config.uuid if target_vm.config else 'N/A'}")
            print(f"   实例UUID: {target_vm.config.instanceUuid if target_vm.config else 'N/A'}")
            print(f"   电源状态: {target_vm.runtime.powerState}")
            print(f"   连接状态: {target_vm.runtime.connectionState}")

            # 硬件配置
            if target_vm.config:
                print(f"\n💻 硬件配置:")
                print(f"   CPU: {target_vm.config.hardware.numCPU} vCPU")
                print(f"   内存: {target_vm.config.hardware.memoryMB} MB")
                print(f"   硬件版本: {target_vm.config.version}")

            # 操作系统
            if target_vm.guest:
                print(f"\n🖥️ 操作系统:")
                print(f"   Guest ID: {target_vm.config.guestId if target_vm.config else 'N/A'}")
                print(f"   完整名称: {target_vm.config.guestFullName if target_vm.config else 'N/A'}")
                print(f"   Guest 状态: {target_vm.guest.guestState}")
                print(f"   IP 地址: {target_vm.guest.ipAddress if target_vm.guest.ipAddress else 'N/A'}")
                print(f"   主机名: {target_vm.guest.hostName if target_vm.guest.hostName else 'N/A'}")

            # 磁盘信息
            if target_vm.config and target_vm.config.hardware:
                disks = [dev for dev in target_vm.config.hardware.device if isinstance(dev, vim.vm.device.VirtualDisk)]

                if disks:
                    print(f"\n💾 磁盘信息 ({len(disks)} 个):")
                    for disk in disks:
                        capacity_gb = disk.capacityInKB / (1024**2)
                        print(f"   - {disk.deviceInfo.label}: {capacity_gb:.1f} GB")

            # 网络信息
            if target_vm.config and target_vm.config.hardware:
                nics = [
                    dev
                    for dev in target_vm.config.hardware.device
                    if isinstance(dev, vim.vm.device.VirtualEthernetCard)
                ]

                if nics:
                    print(f"\n🌐 网络接口 ({len(nics)} 个):")
                    for nic in nics:
                        network_name = nic.backing.network.name if hasattr(nic.backing, "network") else "N/A"
                        mac = nic.macAddress if hasattr(nic, "macAddress") else "N/A"
                        print(f"   - {nic.deviceInfo.label}: {mac} ({network_name})")

            # 快照信息
            if target_vm.snapshot:
                print(f"\n📸 快照信息:")
                print(
                    f"   当前快照: {target_vm.snapshot.currentSnapshot.name if target_vm.snapshot.currentSnapshot else 'None'}"
                )

                def count_snapshots(snapshot_tree):
                    count = len(snapshot_tree)
                    for tree in snapshot_tree:
                        if hasattr(tree, "childSnapshotList"):
                            count += count_snapshots(tree.childSnapshotList)
                    return count

                total_snapshots = count_snapshots(target_vm.snapshot.rootSnapshotList)
                print(f"   快照总数: {total_snapshots}")

            self.test_results.append(("虚拟机详情", True, target_vm.name))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("虚拟机详情", False, str(e)))
            return False

    def test_host_details(self) -> bool:
        """测试10: 获取主机详细信息"""
        self.print_section("测试10: 获取主机详细信息")

        try:
            hosts = self.client.get_hosts()

            if not hosts:
                print("⚠️ 没有找到主机")
                return True

            target_host = hosts[0]

            print(f"\n主机: {target_host.name}")
            print(f"{'-' * 80}")

            # 硬件信息
            hw = target_host.hardware
            print(f"\n🖥️ 硬件信息:")
            print(f"   CPU:")
            print(f"     - 型号: {hw.cpuInfo.model if hasattr(hw.cpuInfo, 'model') else 'N/A'}")
            print(f"     - 插槽数: {hw.cpuInfo.numCpuPackages}")
            print(f"     - 核心数: {hw.cpuInfo.numCpuCores}")
            print(f"     - 线程数: {hw.cpuInfo.numCpuThreads}")
            print(f"     - 频率: {hw.cpuInfo.hz / 1000000:.0f} MHz")
            print(f"   内存: {hw.memorySize / (1024**3):.1f} GB")

            # 运行时信息
            print(f"\n📊 运行时信息:")
            print(f"   连接状态: {target_host.runtime.connectionState}")
            print(f"   电源状态: {target_host.runtime.powerState}")
            print(f"   启动时间: {target_host.runtime.bootTime if target_host.runtime.bootTime else 'N/A'}")

            # 虚拟机统计
            vm_count = len(target_host.vm) if target_host.vm else 0
            print(f"   虚拟机数量: {vm_count}")

            # 网络信息
            if hasattr(target_host.config, "network"):
                vnics = target_host.config.network.vnic if target_host.config.network else []
                print(f"\n🌐 网络接口 ({len(vnics)} 个):")
                for vnic in vnics[:5]:
                    print(f"   - {vnic.device}: {vnic.spec.ip.ipAddress if vnic.spec.ip else 'N/A'}")

            self.test_results.append(("主机详情", True, target_host.name))
            return True

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            self.test_results.append(("主机详情", False, str(e)))
            return False

    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结")

        total = len(self.test_results)
        passed = sum(1 for _, success, _ in self.test_results if success)
        failed = total - passed

        print(f"\n总计: {total} 个测试")
        print(f"通过: {passed} 个 ✅")
        print(f"失败: {failed} 个 ❌")

        print(f"\n详细结果:")
        for name, success, detail in self.test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {status} - {name}: {detail}")

        print(f"\n{'=' * 80}\n")

        return failed == 0

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        self.print_header("vSphere 客户端真实环境测试")

        try:
            # 测试1: 连接
            if not self.test_connection():
                print("\n⚠️ 连接失败，跳过后续测试")
                return False

            # 测试2-8: 各种资源获取
            self.test_about_info()
            self.test_datacenters()
            self.test_clusters()
            self.test_hosts()
            self.test_vms()
            self.test_datastores()
            self.test_networks()

            # 测试9-10: 详细信息
            self.test_vm_details()
            self.test_host_details()

            # 打印总结
            return self.print_summary()

        finally:
            # 确保断开连接
            if self.client.is_connected:
                self.client.disconnect()
                print("✅ 已断开连接")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="vSphere 客户端真实环境测试")
    parser.add_argument("--host", help="vCenter/ESXi 地址（不含 https://）")
    parser.add_argument("--username", help="用户名")
    parser.add_argument("--password", help="密码")
    parser.add_argument("--port", type=int, default=443, help="端口（默认 443）")
    parser.add_argument("--ssl-verify", action="store_true", help="验证 SSL 证书")
    parser.add_argument("--vm-name", help="指定要查看详情的虚拟机名称")

    args = parser.parse_args()

    # 从环境变量或命令行参数获取配置
    host = args.host or os.environ.get("VSPHERE_TEST_HOST")
    username = args.username or os.environ.get("VSPHERE_TEST_USERNAME")
    password = args.password or os.environ.get("VSPHERE_TEST_PASSWORD")

    # 验证必需参数
    if not all([host, username, password]):
        print("❌ 错误: 缺少必需参数\n")
        print("请通过以下方式之一提供 vSphere 连接信息：\n")
        print("方式1: 命令行参数")
        print("  uv run test_vsphere_real.py --host 10.10.100.20 --username admin@vsphere.local --password 'your_pass'")
        print("\n方式2: 环境变量")
        print("  export VSPHERE_TEST_HOST='10.10.100.20'")
        print("  export VSPHERE_TEST_USERNAME='administrator@vsphere.local'")
        print("  export VSPHERE_TEST_PASSWORD='your_password'")
        print("  uv run test_vsphere_real.py")
        print("\n注意:")
        print("  - host 参数不要包含 https:// 前缀")
        print("  - 自签名证书环境不需要 --ssl-verify 参数")
        return False

    # 显示连接信息
    print("\n连接信息:")
    print(f"  主机: {host}")
    print(f"  端口: {args.port}")
    print(f"  用户: {username}")
    print(f"  SSL验证: {'是' if args.ssl_verify else '否'}")

    # 创建测试实例并运行
    tester = VSphereRealTest(
        host=host,
        username=username,
        password=password,
        port=args.port,
        ssl_verify=args.ssl_verify,
    )

    success = tester.run_all_tests()

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
