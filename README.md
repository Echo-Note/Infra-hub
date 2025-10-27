# Infra-hub

## 项目简介

Infra-hub 是一个基于 [xadmin](https://github.com/nineaiyu/xadmin-server) 二次开发的虚拟化平台主机管理系统。感谢 xadmin 项目提供的优秀 RBAC 权限管理框架作为基础。

## 主要功能

本系统专注于虚拟化基础设施管理，提供以下核心功能：

- **虚拟化平台主机管理**：统一管理多个虚拟化平台的主机资源
- **自动化初始化**：集成 cloud-init 等工具，实现服务器自动化初始化
- **配置管理**：支持批量下发配置文件和脚本
- **权限控制**：基于 RBAC 的细粒度权限管理
- **资源监控**：实时监控虚拟机资源使用情况

## 技术栈

- **后端**：Django + Django REST Framework
- **前端**：Vue3 + Element Plus
- **任务队列**：Celery + Redis
- **权限管理**：基于 xadmin 的 RBAC 系统
- **包管理**：uv (快速的 Python 包管理器)

## 快速开始

### 环境要求

- Python 3.12+
- Redis
- MySQL/PostgreSQL
- uv (推荐，用于依赖管理)

### 安装依赖

本项目使用 [uv](https://github.com/astral-sh/uv) 作为包管理工具，它比传统的 pip 更快更高效。

#### 方式一：一键设置（推荐）

```shell
# 运行开发环境设置脚本（自动安装 uv、依赖和 pre-commit）
./setup-dev.sh
```

#### 方式二：手动安装

**1. 安装 uv**

```shell
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

**2. 安装项目依赖**

```shell
# 使用 uv 安装依赖（推荐）
uv sync

# 安装开发依赖（包括 pre-commit、black、isort、flake8 等）
uv sync --dev

# 或使用传统方式
pip install -r requirements.txt
pip install pre-commit black isort flake8
```

### 开发环境设置

#### 1. 安装 pre-commit hooks

项目使用 pre-commit 进行代码格式化和质量检查，包括：
- **black**：Python 代码格式化（行长度 120）
- **isort**：自动排序和组织 import 语句
- **flake8**：代码规范检查，遵循 PEP 8 标准
- **django-upgrade**：Django 代码升级检查
- **通用检查**：删除尾随空格、检查 YAML/JSON 语法等

所有配置已在 `pyproject.toml` 和 `.pre-commit-config.yaml` 中定义。

```shell
# 如果已经安装了开发依赖，直接安装 git hooks
pre-commit install

# 手动运行所有检查（可选）
pre-commit run --all-files

# 更新 pre-commit hooks 到最新版本
pre-commit autoupdate
```

安装后，每次 `git commit` 时会自动运行代码检查和格式化。如果检查失败，需要修复问题后重新提交。

#### 2. 配置文件

复制配置文件模板并根据实际情况修改：

```shell
cp config_example.yml config.yml
# 编辑 config.yml，配置数据库、Redis 等信息
```

### 启动程序

启动之前必须配置好 Redis 和数据库。

#### 方式一：一键启动（推荐，不支持 Windows 平台）

```shell
python manage.py start all -d  # -d 参数是后台运行，如果去掉，则前台运行
```

#### 方式二：手动启动

**1. API 服务**

```shell
python manage.py runserver 0.0.0.0:8896
```

**2. 定时任务**

```shell
# Celery Beat (定时任务调度器)
python -m celery -A server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --max-interval 60

# Celery Worker (任务执行器)
python -m celery -A server worker -P threads -l INFO -c 10 -Q celery --heartbeat-interval 10 -n celery@%h --without-mingle
```

**3. 任务监控（Windows 可能会异常）**

```shell
python -m celery -A server flower -logging=info --url_prefix=api/flower --auto_refresh=False --address=0.0.0.0 --port=5566
```

## 文档

- [数据权限管理](docs/data-permission.md)
- [字段权限管理](docs/field-permission.md)
- [Pre-commit 使用指南](docs/pre-commit-guide.md)
- [xadmin 原始文档](docs/xadmin-README.md)

## 开发规范

### 代码格式化

项目使用以下工具确保代码质量：

- **black**：Python 代码格式化，行长度限制 120 字符
- **isort**：自动排序和组织 import 语句
- **flake8**：代码规范检查，遵循 PEP 8 标准

所有这些工具通过 pre-commit hooks 自动运行，无需手动执行。

### 提交规范

提交代码时，pre-commit 会自动：
1. 格式化 Python 代码
2. 排序 import 语句
3. 检查代码规范
4. 删除尾随空格
5. 检查配置文件语法

如果检查未通过，修复后需要重新 `git add` 并提交。

## 注意事项

⚠️ **Windows 平台限制**：Windows 上面无法正常运行 celery flower，导致任务监控无法正常使用，请使用 Linux 或 macOS 环境开发部署。

⚠️ **数据库迁移**：首次运行前需要执行 `python manage.py migrate` 初始化数据库。

⚠️ **代码提交**：首次克隆项目后，请务必运行 `pre-commit install` 安装 git hooks。

## 致谢

本项目基于 [xadmin-server](https://github.com/nineaiyu/xadmin-server) 进行二次开发，感谢原作者的贡献。

## License

本项目遵循原项目的开源协议。
