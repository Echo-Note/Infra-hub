# 安装指南

本文档详细说明如何安装和部署 Infra-hub。

## 环境准备

### 系统要求

- **操作系统**：Linux（推荐）、macOS
- **Python**：3.12 或更高版本
- **数据库**：MySQL 8.0+ 或 PostgreSQL 12+
- **缓存**：Redis 5.0+
- **内存**：最低 2GB，推荐 4GB+
- **磁盘**：最低 10GB

⚠️ **注意**：Windows 系统不支持 Celery Flower，建议使用 Linux 或 macOS。

### 依赖服务

#### 1. 数据库（二选一）

**MySQL**

```bash
# Ubuntu/Debian
sudo apt install mysql-server mysql-client libmysqlclient-dev

# CentOS/RHEL
sudo yum install mysql-server mysql-devel

# macOS
brew install mysql
```

**PostgreSQL（推荐使用 TimescaleDB 扩展）**

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# 安装 TimescaleDB（可选，用于时序数据）
# https://docs.timescale.com/install/latest/
```

#### 2. Redis

```bash
# Ubuntu/Debian
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis

# macOS
brew install redis

# 启动 Redis
sudo systemctl start redis  # Linux
brew services start redis   # macOS
```

## 安装步骤

### 方式一：一键安装（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Echo-Note/Infra-hub.git
cd Infra-hub

# 2. 运行安装脚本
./setup-dev.sh

# 3. 配置数据库
cp config_example.yml config.yml
vim config.yml  # 修改数据库和 Redis 配置

# 4. 初始化数据库
python manage.py migrate

# 5. 创建超级用户
python manage.py createsuperuser

# 6. 启动服务
python manage.py start all -d
```

### 方式二：手动安装

#### 1. 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

#### 2. 安装项目依赖

```bash
# 使用 uv 安装（推荐）
uv sync

# 安装开发依赖
uv sync --dev

# 或使用 pip
pip install -r requirements.txt
```

#### 3. 安装 pre-commit hooks

```bash
# 安装 pre-commit
uv pip install pre-commit

# 安装 git hooks
pre-commit install

# 测试运行
pre-commit run --all-files
```

#### 4. 配置文件

```bash
# 复制配置模板
cp config_example.yml config.yml

# 编辑配置文件
vim config.yml
```

配置示例：

```yaml
# 数据库配置
DB_ENGINE: mysql  # 或 postgresql
DB_HOST: 127.0.0.1
DB_PORT: 3306
DB_DATABASE: infra_hub
DB_USER: root
DB_PASSWORD: your_password

# Redis 配置
REDIS_HOST: 127.0.0.1
REDIS_PORT: 6379
REDIS_PASSWORD: ""

# Django 配置
SECRET_KEY: "your-secret-key-here"
DEBUG: False
```

#### 5. 数据库初始化

```bash
# 执行迁移
python manage.py migrate

# 加载初始数据（可选）
python manage.py loaddata loadjson/systemconfig.json
python manage.py loaddata loadjson/menu.json

# 创建超级用户
python manage.py createsuperuser
```

## 启动服务

### 方式一：一键启动

```bash
# 后台运行所有服务
python manage.py start all -d

# 查看服务状态
python manage.py status

# 停止服务
python manage.py stop all
```

### 方式二：手动启动

#### 1. 启动 Django API 服务

```bash
# 开发环境
python manage.py runserver 0.0.0.0:8896

# 生产环境（使用 gunicorn）
gunicorn server.wsgi:application \
    --bind 0.0.0.0:8896 \
    --workers 4 \
    --threads 2 \
    --timeout 120
```

#### 2. 启动 Celery Worker

```bash
python -m celery -A server worker \
    -P threads \
    -l INFO \
    -c 10 \
    -Q celery \
    --heartbeat-interval 10 \
    -n celery@%h \
    --without-mingle
```

#### 3. 启动 Celery Beat（定时任务）

```bash
python -m celery -A server beat \
    -l INFO \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --max-interval 60
```

#### 4. 启动 Flower（任务监控，可选）

```bash
python -m celery -A server flower \
    -logging=info \
    --url_prefix=api/flower \
    --auto_refresh=False \
    --address=0.0.0.0 \
    --port=5566
```

## 生产环境部署

### 使用 Docker Compose

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用 Nginx 反向代理

Nginx 配置示例：

```nginx
upstream infra_hub {
    server 127.0.0.1:8896;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://infra_hub;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/Infra-hub/static/;
    }

    location /media/ {
        alias /path/to/Infra-hub/media/;
    }
}
```

### 使用 Systemd 管理服务

创建服务文件 `/etc/systemd/system/infra-hub.service`：

```ini
[Unit]
Description=Infra-hub API Service
After=network.target mysql.service redis.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/Infra-hub
ExecStart=/path/to/venv/bin/gunicorn server.wsgi:application \
    --bind 0.0.0.0:8896 \
    --workers 4
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start infra-hub
sudo systemctl enable infra-hub
sudo systemctl status infra-hub
```

## 验证安装

访问以下 URL 验证服务是否正常：

- **API 文档**：http://localhost:8896/api/swagger/
- **管理后台**：http://localhost:8896/admin/
- **Flower 监控**：http://localhost:5566/api/flower/

## 常见问题

### 1. 数据库连接失败

检查配置文件中的数据库连接信息，确保数据库服务已启动。

```bash
# MySQL
sudo systemctl status mysql

# PostgreSQL
sudo systemctl status postgresql
```

### 2. Redis 连接失败

```bash
# 检查 Redis 状态
sudo systemctl status redis

# 测试连接
redis-cli ping
```

### 3. 端口被占用

```bash
# 查看端口占用
lsof -i :8896

# 修改端口配置
vim config.yml
```

### 4. 依赖安装失败

```bash
# 清理缓存重新安装
uv cache clean
uv sync --reinstall
```

## 下一步

- [虚拟化中心使用指南](virt-center-guide.md)
- [开发指南](development.md)
- [API 接口文档](api-reference.md)
