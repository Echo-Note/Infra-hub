#!/bin/bash
# 开发环境快速设置脚本

set -e

echo "====================================="
echo "Infra-hub 开发环境设置"
echo "====================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "当前 Python 版本: $python_version"

# 检查是否安装了 uv
if ! command -v uv &> /dev/null; then
    echo ""
    echo "❌ 未检测到 uv，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv 安装完成"
else
    echo "✅ uv 已安装"
fi

# 安装项目依赖
echo ""
echo "正在安装项目依赖..."
uv sync --dev

# 安装 pre-commit hooks
echo ""
echo "正在安装 pre-commit hooks..."
uv run pre-commit install

echo ""
echo "====================================="
echo "✅ 开发环境设置完成！"
echo "====================================="
echo ""
echo "接下来的步骤："
echo "1. 复制配置文件: cp config_example.yml config.yml"
echo "2. 编辑 config.yml 配置数据库和 Redis"
echo "3. 运行数据库迁移: python manage.py migrate"
echo "4. 创建超级用户: python manage.py createsuperuser"
echo "5. 启动开发服务器: python manage.py start all -d"
echo ""
echo "提示："
echo "- 每次 git commit 会自动运行代码检查和格式化"
echo "- 手动运行检查: pre-commit run --all-files"
echo "- 更新 hooks: pre-commit autoupdate"
echo ""
