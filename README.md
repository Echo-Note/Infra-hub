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

## 快速开始

### 环境要求

- Python 3.8+
- Redis
- MySQL/PostgreSQL

### 启动程序

启动之前必须配置好 Redis 和数据库。

#### 一键启动（不支持 Windows 平台）

```shell
python manage.py start all -d  # -d 参数是后台运行，如果去掉，则前台运行
```

#### 手动启动

1. API 服务

```shell
python manage.py runserver 0.0.0.0:8896
```

2. 定时任务

```shell
python -m celery -A server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --max-interval 60
python -m celery -A server worker -P threads -l INFO -c 10 -Q celery --heartbeat-interval 10 -n celery@%h --without-mingle
```

3. 任务监控（Windows 可能会异常）

```shell
python -m celery -A server flower -logging=info --url_prefix=api/flower --auto_refresh=False --address=0.0.0.0 --port=5566
```

## 文档

- [数据权限管理](docs/data-permission.md)
- [字段权限管理](docs/field-permission.md)
- [xadmin 原始文档](docs/xadmin-README.md)

## 注意事项

⚠️ Windows 上面无法正常运行 celery flower，导致任务监控无法正常使用，请使用 Linux 环境开发部署。

## 致谢

本项目基于 [xadmin-server](https://github.com/nineaiyu/xadmin-server) 进行二次开发，感谢原作者的贡献。

## License

本项目遵循原项目的开源协议。
