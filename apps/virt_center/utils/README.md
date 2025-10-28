# vSphere 客户端工具

## 文件说明

- `vsphere_client.py` - vSphere 客户端封装类
- `test_vsphere_real.py` - 真实环境测试脚本（独立运行）

## 快速开始

### 1. 基本使用

```python
from vsphere_client import VSphereClient

# 创建客户端
client = VSphereClient(
    host='10.10.100.20',  # 不要包含 https:// 前缀
    username='administrator@vsphere.local',
    password='your_password',
    port=443,
    ssl_verify=False,  # 自签名证书使用 False
)

# 使用上下文管理器（推荐）
with client:
    # 获取版本信息
    about = client.get_about_info()
    print(about)

    # 获取虚拟机列表
    vms = client.get_vms()
    for vm in vms:
        print(f"{vm.name}: {vm.runtime.powerState}")
```

### 2. 测试连接

#### 方式一：直接运行脚本

编辑 `vsphere_client.py` 底部的测试代码：

```python
if __name__ == '__main__':
    import os
    client = VSphereClient(
        host=os.environ.get("vsphere_host"),
        username=os.environ.get("vsphere_username"),
        password=os.environ.get("vsphere_password"),
        port=443,
        ssl_verify=False,
    )
    # ...
```

然后设置环境变量并运行：

```bash
export vsphere_host='10.10.100.20'
export vsphere_username='administrator@vsphere.local'
export vsphere_password='your_password'

python apps/virt_center/utils/vsphere_client.py
```

#### 方式二：运行测试脚本

使用独立的测试脚本（推荐）：

```bash
# 使用环境变量
export VSPHERE_TEST_HOST='10.10.100.20'
export VSPHERE_TEST_USERNAME='administrator@vsphere.local'
export VSPHERE_TEST_PASSWORD='your_password'

python apps/virt_center/utils/test_vsphere_real.py

# 或使用命令行参数
python apps/virt_center/utils/test_vsphere_real.py \
    --host 10.10.100.20 \
    --username 'administrator@vsphere.local' \
    --password 'your_password'

# 查看特定虚拟机详情
python apps/virt_center/utils/test_vsphere_real.py \
    --vm-name 'my-vm-name'
```

## API 方法

### 连接管理

```python
# 连接
client.connect()

# 断开
client.disconnect()

# 检查连接状态
if client.is_connected:
    print("已连接")
```

### 获取资源

```python
# 获取版本信息
about = client.get_about_info()

# 获取数据中心
datacenters = client.get_datacenters()

# 获取集群
clusters = client.get_clusters()
# 或指定数据中心
clusters = client.get_clusters(datacenter=dc)

# 获取主机
hosts = client.get_hosts()

# 获取虚拟机
vms = client.get_vms()

# 获取数据存储
datastores = client.get_datastores()

# 获取网络
networks = client.get_networks()
```

## 测试输出示例

```
================================================================================
 vSphere 客户端真实环境测试
================================================================================

▶ 测试1: 连接到 vSphere
--------------------------------------------------------------------------------
✅ 连接成功
   耗时: 1.23 秒

▶ 测试2: 获取 vSphere 版本信息
--------------------------------------------------------------------------------
✅ 成功获取版本信息:
   名称:      VMware vCenter Server
   完整名称:  VMware vCenter Server 7.0.3
   版本:      7.0.3
   构建号:    18778458

▶ 测试6: 获取虚拟机列表
--------------------------------------------------------------------------------
✅ 成功获取 150 个虚拟机 (耗时: 2.45s):

   状态统计:
   - 运行中: 120
   - 已关机: 28
   - 已挂起: 2

   虚拟机详情 (前20个):
   1. 🟢 web-server-01
      - CPU: 4 vCPU, 内存: 8192 MB
      - 操作系统: Ubuntu Linux (64-bit)
      - 状态: poweredOn
   ...

================================================================================
 测试总结
================================================================================

总计: 10 个测试
通过: 10 个 ✅
失败: 0 个 ❌
```

## 常见问题

### 1. SSL 错误

```
❌ SSL 错误: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**解决方案**: 设置 `ssl_verify=False`

### 2. 连接超时

```
❌ 连接失败: [Errno 60] Operation timed out
```

**检查**:
- 网络连通性: `ping 10.10.100.20`
- 端口开放: `telnet 10.10.100.20 443`
- 防火墙规则

### 3. 登录失败

```
❌ 登录失败: Cannot complete login due to an incorrect user name or password
```

**检查**:
- 用户名格式: `administrator@vsphere.local`
- 密码是否正确
- 账号是否被锁定

### 4. 主机地址格式错误

```python
# ❌ 错误
host='https://10.10.100.20'

# ✅ 正确
host='10.10.100.20'
```

## 开发建议

1. **使用上下文管理器**: 自动处理连接和断开
2. **错误处理**: 总是捕获可能的异常
3. **日志记录**: 使用 logging 记录重要操作
4. **性能优化**: 批量获取数据，减少 API 调用次数

## 参考文档

- [PyVmomi GitHub](https://github.com/vmware/pyvmomi)
- [vSphere API 文档](https://developer.vmware.com/apis/vsphere-automation/latest/)
- [vSphere SDK 示例](https://github.com/vmware/pyvmomi-community-samples)
