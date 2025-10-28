# Infra-hub

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 项目简介

Infra-hub 是一个基于 [xadmin](https://github.com/nineaiyu/xadmin-server) 二次开发的虚拟化平台主机管理系统，专注于 VMware vSphere/vCenter 环境的统一管理和自动化运维。

## 核心特性

- 🎯 **虚拟化平台管理**：支持 vCenter/ESXi 的统一接入和管理
- 🖥️ **主机资源管理**：ESXi 主机的监控、配置和维护
- 💻 **虚拟机管理**：虚拟机的创建、配置、快照和生命周期管理
- 💾 **存储管理**：数据存储的监控和容量管理
- 📊 **资源监控**：实时采集和展示性能指标
- 🔐 **权限控制**：基于 RBAC 的细粒度权限管理
- 🔒 **安全加密**：敏感信息（密码、密钥）自动加密存储

## 技术架构

- **后端框架**：Django 5.2 + Django REST Framework
- **数据库**：MySQL/PostgreSQL（支持 TimescaleDB 时序扩展）
- **任务队列**：Celery + Redis
- **虚拟化接口**：PyVmomi（vSphere API）
- **权限系统**：基于 xadmin 的 RBAC
- **包管理**：uv（高性能 Python 包管理器）

## 快速开始

### 环境要求

- Python 3.12+
- Redis 5.0+
- MySQL 8.0+ / PostgreSQL 12+
- uv（推荐）

### 一键安装

```bash
# 克隆项目
git clone https://github.com/Echo-Note/Infra-hub.git
cd Infra-hub

# 自动安装依赖和配置开发环境
./setup-dev.sh

# 配置数据库连接
cp config_example.yml config.yml
vim config.yml

# 初始化数据库
python manage.py migrate

# 启动服务
python manage.py start all -d
```

更多安装和部署细节，请参考 [安装指南](docs/installation.md)

## 文档导航

### 用户文档
- [安装指南](docs/installation.md) - 详细的安装和部署说明
- [虚拟化中心使用](docs/virt-center-guide.md) - vSphere 平台管理指南

### 开发文档
- [开发指南](docs/development.md) - 开发环境配置和规范
- [数据模型设计](docs/data-models.md) - 数据库模型详细说明
- [API 接口文档](docs/api-reference.md) - RESTful API 使用文档

### 权限管理
- [数据权限管理](docs/data-permission.md)
- [字段权限管理](docs/field-permission.md)

### 工具和规范
- [Pre-commit 使用指南](docs/pre-commit-guide.md)
- [xadmin 原始文档](docs/xadmin-README.md)

## 项目结构

```
Infra-hub/
├── apps/                      # 应用模块
│   ├── virt_center/          # 虚拟化中心（核心模块）
│   │   ├── models/           # 数据模型
│   │   ├── views/            # 视图控制器
│   │   ├── serializers/      # 序列化器
│   │   └── utils/            # 工具类（vSphere 客户端）
│   ├── common/               # 公共模块
│   │   ├── utils/            # 工具函数（加密、缓存等）
│   │   └── fields/           # 自定义字段（加密字段）
│   └── system/               # 系统管理（用户、权限）
├── server/                    # 项目配置
├── docs/                      # 文档
└── manage.py                  # Django 管理脚本
```

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目！

在提交 PR 前，请确保：
- 代码通过所有 pre-commit 检查
- 添加了必要的测试
- 更新了相关文档

详细的贡献指南请参考 [CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 致谢

- 感谢 [xadmin-server](https://github.com/nineaiyu/xadmin-server) 提供的优秀 RBAC 权限管理框架
- 感谢 VMware 提供的 [PyVmomi](https://github.com/vmware/pyvmomi) Python SDK

## License

本项目遵循原项目的开源协议。
