# 贡献指南

感谢你对 Infra-hub 项目的关注！本文档将帮助你快速上手开发。

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/Echo-Note/Infra-hub.git
cd Infra-hub
```

### 2. 安装 uv

推荐使用 [uv](https://github.com/astral-sh/uv) 管理 Python 依赖，它比 pip 更快：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 3. 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 4. 安装 pre-commit

```bash
# 使用 uv
uv pip install pre-commit

# 或使用 pip
pip install pre-commit

# 安装 git hooks
pre-commit install
```

### 5. 配置项目

```bash
# 复制配置文件
cp config_example.yml config.yml

# 编辑 config.yml，配置数据库和 Redis 连接信息
```

### 6. 初始化数据库

```bash
python manage.py migrate
python manage.py createsuperuser  # 创建管理员账号
```

## 代码规范

### 自动化代码检查

项目使用 pre-commit 进行自动化代码检查和格式化，包括：

- **black**：Python 代码格式化（行长度 120）
- **isort**：自动排序 import 语句
- **flake8**：代码规范检查（PEP 8）
- **django-upgrade**：Django 代码升级建议
- **基础检查**：删除尾随空格、文件结尾换行、YAML/JSON 语法等

### 手动运行检查

```bash
# 检查所有文件
pre-commit run --all-files

# 检查暂存的文件
pre-commit run

# 检查特定文件
pre-commit run --files apps/demo/views.py
```

### 代码提交流程

1. **修改代码**

```bash
# 编辑代码
vim apps/demo/views.py
```

2. **添加到暂存区**

```bash
git add apps/demo/views.py
```

3. **提交代码**

```bash
git commit -m "feat: 添加新功能"
```

pre-commit 会自动运行检查：
- ✅ 如果检查通过，代码正常提交
- ❌ 如果检查失败，会自动修复部分问题（如格式化），需要重新 add 并提交

4. **重新提交（如果需要）**

```bash
git add .
git commit -m "feat: 添加新功能"
```

### 提交信息规范

推荐使用语义化提交信息：

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具链更新

示例：
```bash
git commit -m "feat: 添加虚拟机批量操作功能"
git commit -m "fix: 修复主机列表分页问题"
git commit -m "docs: 更新 README 安装说明"
```

## 开发工作流

### 分支管理

- `main`/`master`: 生产环境分支
- `dev`: 开发分支
- `feature/*`: 功能开发分支
- `fix/*`: bug 修复分支

### 开发流程

1. 从 dev 分支创建功能分支

```bash
git checkout dev
git pull
git checkout -b feature/your-feature-name
```

2. 开发并提交代码

```bash
# 开发过程中多次提交
git add .
git commit -m "feat: 实现某功能"
```

3. 推送到远程

```bash
git push origin feature/your-feature-name
```

4. 创建 Pull Request

向 `dev` 分支提交 PR，等待代码审查

## 常见问题

### pre-commit 检查失败怎么办？

1. **格式化问题**：black 和 isort 会自动修复，重新 `git add` 即可
2. **flake8 错误**：需要手动修复代码问题
3. **跳过检查**（不推荐）：`git commit --no-verify`

### uv 安装依赖慢怎么办？

```bash
# 使用国内镜像
export UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
uv sync
```

### 如何添加新的依赖？

```bash
# 使用 uv 添加（推荐）
uv add package-name

# 或手动编辑 pyproject.toml 和 requirements.txt
# 然后运行
uv sync
```

## 测试

```bash
# 运行测试
python manage.py test

# 运行特定应用的测试
python manage.py test apps.demo

# 生成测试覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html  # 生成 HTML 报告
```

## 需要帮助？

如有问题，欢迎：
- 提交 Issue
- 加入讨论
- 查看项目文档

感谢你的贡献！ 🎉
