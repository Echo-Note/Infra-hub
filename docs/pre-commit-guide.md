# Pre-commit 使用指南

## 简介

本项目使用 [pre-commit](https://pre-commit.com/) 来管理和维护多语言的 pre-commit hooks，确保代码质量和一致性。

## 快速开始

### 安装

```bash
# 安装开发依赖（包含 pre-commit）
uv sync --dev

# 安装 git hooks
pre-commit install
```

### 基本使用

```bash
# 手动对所有文件运行检查
pre-commit run --all-files

# 只对暂存的文件运行检查
pre-commit run

# 对特定文件运行检查
pre-commit run --files path/to/file.py

# 更新 hooks 到最新版本
pre-commit autoupdate
```

## 配置的 Hooks

项目配置了以下 hooks（在 `.pre-commit-config.yaml` 中定义）：

### 1. 通用检查 (pre-commit-hooks)

- **trailing-whitespace**: 删除行尾的空格
- **end-of-file-fixer**: 确保文件以换行符结尾
- **check-yaml**: 检查 YAML 文件语法
- **check-json**: 检查 JSON 文件语法
- **check-toml**: 检查 TOML 文件语法
- **check-merge-conflict**: 检查是否有合并冲突标记
- **debug-statements**: 检查 Python debug 语句（如 `pdb.set_trace()`）
- **check-added-large-files**: 检查大文件（默认 1MB）

### 2. Import 排序 (isort)

自动排序和组织 Python import 语句，配置：
- 兼容 black 格式
- 行长度 120
- 识别 Django 相关导入
- 跳过 migrations 目录

### 3. 代码格式化 (black)

Python 代码自动格式化工具，配置：
- 行长度：120 字符
- 目标版本：Python 3.12
- 排除目录：migrations, static, media, data, tmp

### 4. 代码检查 (flake8)

Python 代码风格检查，配置：
- 最大行长度：120
- 忽略规则：E203（black 兼容）、W503（换行符位置）
- 附加插件：flake8-bugbear、flake8-comprehensions

### 5. Django 升级检查 (django-upgrade)

检查并建议 Django 代码升级到 5.0 版本的写法

## 工作流程

### 正常提交流程

```bash
# 1. 修改代码
vim apps/demo/views.py

# 2. 添加到暂存区
git add apps/demo/views.py

# 3. 提交（会自动运行 pre-commit）
git commit -m "feat: 添加新功能"

# 如果检查通过，提交成功
# 如果检查失败，pre-commit 会自动修复部分问题（如格式化）
```

### 检查失败后的处理

如果 pre-commit 检查失败：

```bash
# 1. 查看 pre-commit 的输出，了解哪些检查失败
# 2. 部分问题会被自动修复（如格式化），重新添加修改的文件
git add apps/demo/views.py

# 3. 有些问题需要手动修复（如代码规范问题）
# 修复后重新添加文件
git add apps/demo/views.py

# 4. 重新提交
git commit -m "feat: 添加新功能"
```

## 跳过检查（不推荐）

在特殊情况下，可以跳过 pre-commit 检查：

```bash
# 跳过所有 pre-commit 检查
git commit --no-verify -m "紧急修复"

# 不推荐！只在紧急情况下使用
```

## 常见问题

### Q1: 如何跳过特定的 hook？

可以设置 `SKIP` 环境变量：

```bash
SKIP=flake8 git commit -m "提交信息"
```

### Q2: 如何临时禁用 pre-commit？

```bash
# 卸载 hooks
pre-commit uninstall

# 重新安装
pre-commit install
```

### Q3: pre-commit 运行很慢怎么办？

Pre-commit 会缓存环境，首次运行会慢一些。后续运行会快很多。

```bash
# 清理缓存
pre-commit clean

# 重新安装
pre-commit install
```

### Q4: 如何更新 hooks 版本？

```bash
# 自动更新到最新稳定版本
pre-commit autoupdate

# 查看配置文件的变更
git diff .pre-commit-config.yaml
```

## 工具配置

所有工具的详细配置都在 `pyproject.toml` 中：

### Black 配置

```toml
[tool.black]
line-length = 120
target-version = ['py312']
extend-exclude = '''/(migrations|static|media|data|tmp)/'''
```

### isort 配置

```toml
[tool.isort]
profile = "black"
line_length = 120
known_first_party = ["apps", "server"]
known_django = ["django"]
```

### Flake8 配置

```toml
[tool.flake8]
max-line-length = 120
extend-ignore = ["E203", "W503", "E501"]
exclude = ["migrations", "static", "media", "data", "tmp"]
```

## CI/CD 集成

在 CI/CD 流程中运行 pre-commit：

```yaml
# GitHub Actions 示例
- name: Run pre-commit
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

## 最佳实践

1. **定期更新**: 定期运行 `pre-commit autoupdate` 更新 hooks
2. **全量检查**: 定期运行 `pre-commit run --all-files` 对整个项目检查
3. **不要跳过**: 避免使用 `--no-verify`，保持代码质量
4. **团队协作**: 确保所有团队成员都安装了 pre-commit

## 参考资源

- [Pre-commit 官方文档](https://pre-commit.com/)
- [Black 文档](https://black.readthedocs.io/)
- [isort 文档](https://pycqa.github.io/isort/)
- [Flake8 文档](https://flake8.pycqa.org/)
