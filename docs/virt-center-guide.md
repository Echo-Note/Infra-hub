# 虚拟化中心使用指南

本文档介绍如何使用 Infra-hub 管理 VMware vSphere 虚拟化平台。

## 概述

虚拟化中心（virt_center）是 Infra-hub 的核心模块，提供对 VMware vSphere/vCenter 平台的统一管理能力。

### 主要功能

- 🔌 **平台管理**：连接和管理多个 vCenter/ESXi 平台
- 🖥️ **主机监控**：实时监控 ESXi 主机状态和资源使用
- 💻 **虚拟机管理**：虚拟机的创建、配置、快照和生命周期管理
- 💾 **存储管理**：数据存储的容量监控和管理
- 📊 **性能监控**：采集和展示 CPU、内存、磁盘、网络指标
- 🔒 **安全加密**：敏感凭据自动加密存储

## 快速开始

### 1. 添加 vSphere 平台

#### 通过 Web 界面

1. 登录系统，进入"虚拟化中心" > "平台管理"
2. 点击"添加平台"按钮
3. 填写平台信息：
   - 平台名称：如"生产环境 vCenter"
   - 平台类型：选择 vCenter 或 ESXi
   - 主机地址：vCenter/ESXi 的 IP 或域名
   - 端口：默认 443
   - SSL 验证：是否验证 SSL 证书
4. 点击"下一步"，填写认证信息：
   - 用户名：如 `administrator@vsphere.local`
   - 密码：管理员密码（自动加密存储）
5. 测试连接成功后，保存配置

#### 通过代码

```python
from apps.virt_center.models import Platform, PlatformCredential

# 创建平台
platform = Platform.objects.create(
    name="生产环境 vCenter",
    platform_type=Platform.PlatformType.VCENTER,
    host="10.10.100.20",
    port=443,
    is_ssl=True,
    ssl_verify=False,
    datacenter="Datacenter1",
    is_active=True,
)

# 创建认证凭据（密码自动加密）
credential = PlatformCredential.objects.create(
    platform=platform,
    auth_type=PlatformCredential.AuthType.PASSWORD,
    username="administrator@vsphere.local",
    password="YourPassword123",  # 会自动加密存储
)
```

### 2. 连接测试

使用 vSphere 客户端工具测试连接：

```python
from apps.virt_center.models import Platform
from apps.virt_center.utils import get_vsphere_client

# 获取平台
platform = Platform.objects.get(name="生产环境 vCenter")

# 创建客户端并测试连接
with get_vsphere_client(platform) as client:
    # 获取 vSphere 版本信息
    about = client.get_about_info()
    print(f"vSphere 版本: {about['version']}")
    print(f"构建号: {about['build']}")

    # 获取数据中心列表
    datacenters = client.get_datacenters()
    for dc in datacenters:
        print(f"数据中心: {dc.name}")
```

### 3. 同步数据

#### 手动同步

```python
from apps.virt_center.tasks import sync_platform_data

# 同步平台数据
platform_id = "your-platform-uuid"
sync_platform_data.delay(platform_id)
```

#### 配置定时同步

通过 Django Admin 配置 Celery Beat 定时任务：

1. 进入"系统管理" > "定时任务"
2. 创建新任务：
   - 名称：同步 vCenter 数据
   - 任务：`apps.virt_center.tasks.sync_platform_data`
   - 参数：`["platform-uuid"]`
   - 调度：每 5 分钟执行一次

## 核心功能详解

### 平台管理

#### 支持的平台类型

- **vCenter**：推荐，可管理多台 ESXi 主机
- **ESXi**：直接连接单台 ESXi 主机

#### 平台状态

- **未连接**：尚未建立连接
- **已连接**：正常连接
- **连接异常**：无法连接或认证失败
- **维护中**：手动设置为维护状态

### 主机管理

#### 主机信息

系统会自动采集以下 ESXi 主机信息：

- **基本信息**：主机名、IP、UUID
- **硬件信息**：CPU 型号、核心数、内存大小
- **版本信息**：ESXi 版本、构建号
- **集群信息**：所属集群、数据中心
- **状态信息**：运行状态、电源状态、连接状态

#### 资源监控

- **CPU**：使用率、频率、就绪率
- **内存**：使用率、已用内存、活动内存
- **网络**：接收/发送速率、包数
- **磁盘**：读/写速率、IOPS、延迟

### 虚拟机管理

#### 虚拟机信息

- **基本信息**：名称、UUID、操作系统
- **硬件配置**：vCPU、内存、磁盘
- **网络配置**：IP 地址、MAC 地址、网卡类型
- **状态信息**：电源状态、运行状态、Tools 状态
- **位置信息**：所在主机、集群、资源池

#### 虚拟机操作

```python
from apps.virt_center.models import VirtualMachine
from apps.virt_center.utils import get_vsphere_client

vm = VirtualMachine.objects.get(name="test-vm-01")
platform = vm.platform

with get_vsphere_client(platform) as client:
    # 查找虚拟机对象
    vms = client.get_vms()
    vm_obj = next((v for v in vms if v.config.uuid == vm.uuid), None)

    if vm_obj:
        # 开机
        if vm_obj.runtime.powerState == "poweredOff":
            task = vm_obj.PowerOn()

        # 关机
        if vm_obj.runtime.powerState == "poweredOn":
            task = vm_obj.PowerOff()

        # 重启
        task = vm_obj.ResetVM_Task()

        # 创建快照
        task = vm_obj.CreateSnapshot_Task(
            name="快照名称",
            description="快照描述",
            memory=False,
            quiesce=True
        )
```

### 存储管理

#### 数据存储类型

- **VMFS**：VMware 文件系统
- **NFS**：网络文件系统
- **vSAN**：VMware vSAN
- **vVol**：虚拟卷

#### 容量监控

```python
from apps.virt_center.models import DataStore

# 查询存储使用情况
datastores = DataStore.objects.filter(platform=platform)
for ds in datastores:
    print(f"存储: {ds.name}")
    print(f"总容量: {ds.capacity_gb} GB")
    print(f"已用: {ds.used_gb} GB")
    print(f"使用率: {ds.usage_percent}%")
```

### 性能监控

#### 监控指标

监控数据存储在 `HostMetrics` 和 `VMMetrics` 表中：

```python
from apps.virt_center.models import Host, HostMetrics
from django.utils import timezone
from datetime import timedelta

# 查询主机最近1小时的监控数据
host = Host.objects.get(name="esxi-01")
end_time = timezone.now()
start_time = end_time - timedelta(hours=1)

metrics = HostMetrics.objects.filter(
    host=host,
    collected_at__gte=start_time,
    collected_at__lte=end_time
).order_by('collected_at')

for m in metrics:
    print(f"{m.collected_at}: CPU {m.cpu_usage_percent}%, 内存 {m.memory_usage_percent}%")
```

#### 使用 TimescaleDB（推荐）

对于大规模环境，推荐使用 TimescaleDB 存储时序数据：

```python
# 安装 TimescaleDB 后，将监控表转换为 hypertable
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        "SELECT create_hypertable('virt_host_metrics', 'collected_at', if_not_exists => TRUE)"
    )
    cursor.execute(
        "SELECT create_hypertable('virt_vm_metrics', 'collected_at', if_not_exists => TRUE)"
    )
```

## 安全最佳实践

### 1. 凭据管理

- ✅ 密码和密钥自动加密存储（使用 Fernet 对称加密）
- ✅ 加密密钥基于 Django SECRET_KEY 派生
- ✅ 支持凭据轮换和更新
- ❌ 不要在代码中硬编码密码

### 2. SSL 证书

生产环境建议启用 SSL 证书验证：

```python
platform.ssl_verify = True
platform.save()
```

### 3. 权限控制

- 使用 RBAC 控制不同用户的访问权限
- 限制敏感操作（删除虚拟机、修改配置等）的权限
- 启用操作日志审计

## 故障排查

### 连接失败

```python
# 检查平台连接状态
from apps.virt_center.utils import get_vsphere_client
from apps.virt_center.models import Platform

platform = Platform.objects.get(id="platform-id")

try:
    with get_vsphere_client(platform) as client:
        about = client.get_about_info()
        print("✅ 连接成功")
        print(f"版本: {about['version']}")
except vim.fault.InvalidLogin:
    print("❌ 认证失败，请检查用户名和密码")
except Exception as e:
    print(f"❌ 连接失败: {str(e)}")
```

### 常见错误

1. **InvalidLogin**：用户名或密码错误
2. **SSLCertVerificationError**：SSL 证书验证失败，设置 `ssl_verify=False`
3. **ConnectionRefusedError**：无法连接到主机，检查网络和防火墙
4. **TimeoutError**：连接超时，检查网络延迟

## 性能优化

### 1. 批量操作

使用 bulk_create 和 bulk_update 提高性能：

```python
from apps.virt_center.models import VirtualMachine

vms_to_create = []
for vm_data in vm_list:
    vms_to_create.append(VirtualMachine(**vm_data))

# 批量创建，比逐个 save() 快很多
VirtualMachine.objects.bulk_create(vms_to_create, batch_size=100)
```

### 2. 连接池

对于频繁操作，使用连接池：

```python
# 复用同一个连接
client = get_vsphere_client(platform)
client.connect()

try:
    # 执行多个操作
    hosts = client.get_hosts()
    vms = client.get_vms()
    datastores = client.get_datastores()
finally:
    client.disconnect()
```

### 3. 异步任务

大量数据同步使用 Celery 异步任务：

```python
from apps.virt_center.tasks import sync_vms, sync_hosts

# 异步同步虚拟机
sync_vms.delay(platform_id)

# 异步同步主机
sync_hosts.delay(platform_id)
```

## API 使用示例

详细的 API 文档请参考 [API 接口文档](api-reference.md)。

### 获取平台列表

```http
GET /api/virt-center/platforms/
Authorization: Bearer <your-token>
```

### 获取虚拟机列表

```http
GET /api/virt-center/vms/?platform=<platform-id>
Authorization: Bearer <your-token>
```

### 虚拟机操作

```http
POST /api/virt-center/vms/<vm-id>/power-on/
Authorization: Bearer <your-token>
```

## 下一步

- [数据模型详细说明](data-models.md)
- [API 接口文档](api-reference.md)
- [开发指南](development.md)
