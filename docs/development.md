# 开发指南

本文档面向 Infra-hub 项目的开发者，介绍开发环境配置、开发规范和常见开发任务。

## 开发环境配置

### 系统要求

- Python 3.12+
- Git
- Redis
- MySQL/PostgreSQL
- uv（推荐）

### 快速配置

```bash
# 克隆项目
git clone https://github.com/Echo-Note/Infra-hub.git
cd Infra-hub

# 一键配置开发环境
./setup-dev.sh
```

该脚本会自动完成：
- 安装 uv
- 安装项目依赖和开发依赖
- 安装 pre-commit hooks

### 手动配置

如果自动配置失败，可以手动配置：

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装依赖
uv sync --dev

# 3. 安装 pre-commit
pre-commit install

# 4. 配置数据库
cp config_example.yml config.yml
vim config.yml

# 5. 初始化数据库
python manage.py migrate

# 6. 创建超级用户
python manage.py createsuperuser
```

## 开发工具

### IDE 推荐

**PyCharm / VS Code**

推荐配置：
- 安装 Python 扩展
- 配置代码格式化（Black）
- 配置 linter（Flake8）
- 启用类型检查

### VS Code 配置

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "120"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": ["--max-line-length=120"],
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## 代码规范

### Python 风格指南

项目遵循 PEP 8 规范，并通过以下工具强制执行：

- **Black**: 代码格式化，行长度 120
- **isort**: Import 排序
- **Flake8**: 代码检查

配置详见 `pyproject.toml`：

```toml
[tool.black]
line-length = 120
target-version = ['py312']

[tool.isort]
profile = "black"
line_length = 120
known_first_party = ["apps", "server"]

[tool.flake8]
max-line-length = 120
extend-ignore = ["E203", "W503"]
```

### Django 最佳实践

#### 1. 模型设计

```python
from django.db import models
from apps.common.core.models import DbAuditModel, DbUuidModel

class VirtualMachine(DbUuidModel, DbAuditModel):
    """虚拟机模型"""

    name = models.CharField(
        max_length=128,
        verbose_name="虚拟机名称",
        help_text="虚拟机显示名称",
        db_index=True,
    )

    class Meta:
        db_table = "virt_vm"
        verbose_name = "虚拟机"
        verbose_name_plural = verbose_name
        ordering = ["-created_time"]
        indexes = [
            models.Index(fields=["platform", "status"]),
        ]

    def __str__(self):
        return self.name
```

**要点**：
- 使用基类（DbUuidModel, DbAuditModel）
- 添加 verbose_name 和 help_text（中文）
- 合理使用索引
- 定义 Meta 类
- 重写 `__str__` 方法

#### 2. 序列化器

```python
from rest_framework import serializers
from apps.virt_center.models import VirtualMachine

class VirtualMachineSerializer(serializers.ModelSerializer):
    """虚拟机序列化器"""

    platform_name = serializers.CharField(
        source="platform.name",
        read_only=True,
        help_text="平台名称"
    )

    class Meta:
        model = VirtualMachine
        fields = [
            "id",
            "name",
            "platform",
            "platform_name",
            "status",
            "created_time",
        ]
        read_only_fields = ["id", "created_time"]
```

#### 3. ViewSet

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.virt_center.models import VirtualMachine
from apps.virt_center.serializers import VirtualMachineSerializer

class VirtualMachineViewSet(viewsets.ModelViewSet):
    """虚拟机视图集"""

    queryset = VirtualMachine.objects.all()
    serializer_class = VirtualMachineSerializer

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """启动虚拟机"""
        vm = self.get_object()
        # 业务逻辑
        return Response({"status": "success"})
```

### 敏感信息处理

项目提供了加密字段来自动处理敏感信息：

```python
from apps.common.fields import EncryptedCharField, EncryptedTextField

class PlatformCredential(models.Model):
    password = EncryptedCharField(
        max_length=128,
        verbose_name="密码",
        help_text="自动加密存储"
    )
    ssh_key = EncryptedTextField(
        verbose_name="SSH 私钥",
        help_text="自动加密存储"
    )
```

数据会在保存时自动加密，读取时自动解密。

## 项目结构

```
Infra-hub/
├── apps/                          # Django 应用
│   ├── virt_center/              # 虚拟化中心（核心应用）
│   │   ├── models/               # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── platform.py       # 平台模型
│   │   │   ├── host.py           # 主机模型
│   │   │   ├── vm.py             # 虚拟机模型
│   │   │   ├── storage.py        # 存储模型
│   │   │   ├── monitor.py        # 监控模型
│   │   │   ├── template.py       # 模板模型
│   │   │   └── operation.py      # 操作记录模型
│   │   ├── views/                # 视图
│   │   ├── serializers/          # 序列化器
│   │   ├── utils/                # 工具类
│   │   │   ├── vsphere_client.py # vSphere 客户端
│   │   │   └── ...
│   │   ├── tasks.py              # Celery 任务
│   │   ├── admin.py              # Admin 配置
│   │   └── urls.py               # URL 路由
│   ├── common/                   # 公共模块
│   │   ├── utils/                # 工具函数
│   │   │   ├── crypto.py         # 加密工具
│   │   │   └── ...
│   │   ├── fields/               # 自定义字段
│   │   │   ├── encrypted.py      # 加密字段
│   │   │   └── ...
│   │   └── core/                 # 核心基类
│   └── system/                   # 系统管理
├── server/                        # 项目配置
│   ├── settings/                 # 配置文件
│   ├── celery.py                 # Celery 配置
│   ├── urls.py                   # 根 URL
│   └── wsgi.py                   # WSGI 入口
├── docs/                          # 文档
├── static/                        # 静态文件
├── media/                         # 媒体文件
├── manage.py                      # Django 管理脚本
├── pyproject.toml                 # 项目配置
├── requirements.txt               # 依赖列表
└── .pre-commit-config.yaml        # pre-commit 配置
```

## 常见开发任务

### 创建新应用

```bash
python manage.py startapp new_app apps/new_app
```

### 创建数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations

# 查看 SQL
python manage.py sqlmigrate virt_center 0001

# 执行迁移
python manage.py migrate

# 回滚迁移
python manage.py migrate virt_center 0001
```

### 添加 Celery 任务

```python
# apps/virt_center/tasks.py
from celery import shared_task
from apps.virt_center.models import Platform
from apps.virt_center.utils import get_vsphere_client

@shared_task
def sync_platform_data(platform_id):
    """同步平台数据"""
    platform = Platform.objects.get(id=platform_id)
    client = get_vsphere_client(platform)

    with client:
        # 执行同步逻辑
        vms = client.get_vms()
        # 处理虚拟机数据
        ...

    return {"status": "success", "count": len(vms)}
```

调用任务：

```python
from apps.virt_center.tasks import sync_platform_data

# 异步执行
sync_platform_data.delay(platform_id)

# 定时执行（在 Admin 中配置 PeriodicTask）
```

### 添加管理命令

```python
# apps/virt_center/management/commands/sync_vsphere.py
from django.core.management.base import BaseCommand
from apps.virt_center.models import Platform

class Command(BaseCommand):
    help = '同步 vSphere 数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--platform',
            type=str,
            help='平台名称'
        )

    def handle(self, *args, **options):
        platform_name = options.get('platform')
        # 执行逻辑
        self.stdout.write(
            self.style.SUCCESS(f'成功同步 {platform_name}')
        )
```

使用：

```bash
python manage.py sync_vsphere --platform="生产环境"
```

## 调试技巧

### Django Debug Toolbar

安装和配置（仅开发环境）：

```python
# settings/base.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### 日志配置

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("调试信息")
    logger.info("一般信息")
    logger.warning("警告信息")
    logger.error("错误信息")
```

### Django Shell

```bash
# 启动 Django Shell
python manage.py shell

# 或使用 IPython
pip install ipython
python manage.py shell
```

```python
# 在 Shell 中测试代码
from apps.virt_center.models import Platform
from apps.virt_center.utils import get_vsphere_client

platform = Platform.objects.first()
client = get_vsphere_client(platform)

with client:
    about = client.get_about_info()
    print(about)
```

## 测试

### 编写测试

```python
# apps/virt_center/tests/test_models.py
from django.test import TestCase
from apps.virt_center.models import Platform

class PlatformModelTest(TestCase):
    def setUp(self):
        self.platform = Platform.objects.create(
            name="测试平台",
            platform_type="vcenter",
            host="10.10.100.20",
        )

    def test_connection_url(self):
        expected = "https://10.10.100.20:443"
        self.assertEqual(self.platform.connection_url, expected)
```

### 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行指定应用
python manage.py test apps.virt_center

# 带覆盖率
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # 生成 HTML 报告
```

## 性能优化

### 数据库查询优化

```python
# 使用 select_related 减少查询
vms = VirtualMachine.objects.select_related(
    'platform', 'host'
).all()

# 使用 prefetch_related 优化多对多查询
platforms = Platform.objects.prefetch_related(
    'vms', 'hosts'
).all()

# 使用 only/defer 只查询需要的字段
vms = VirtualMachine.objects.only(
    'id', 'name', 'status'
).all()
```

### 缓存策略

```python
from django.core.cache import cache

def get_platform_stats(platform_id):
    cache_key = f"platform_stats_{platform_id}"
    stats = cache.get(cache_key)

    if stats is None:
        # 计算统计数据
        stats = calculate_stats(platform_id)
        cache.set(cache_key, stats, timeout=300)  # 5分钟

    return stats
```

## 部署

### 收集静态文件

```bash
python manage.py collectstatic --noinput
```

### 生产环境配置

```python
# config.yml
DEBUG: False
SECRET_KEY: "your-production-secret-key"
ALLOWED_HOSTS:
  - your-domain.com
```

## 参考资源

- [Django 官方文档](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery 文档](https://docs.celeryproject.org/)
- [PyVmomi 文档](https://github.com/vmware/pyvmomi)

## 获取帮助

遇到问题？

1. 查看 [FAQ](FAQ.md)
2. 搜索 [Issues](https://github.com/Echo-Note/Infra-hub/issues)
3. 创建新 Issue
4. 查阅项目文档

---

Happy Coding! 🚀
