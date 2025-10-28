# 贡献指南

感谢你对 Infra-hub 项目的关注！我们欢迎任何形式的贡献，包括但不限于：

- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复或新功能

## 行为准则

在参与本项目时，请遵守以下准则：

- 尊重所有贡献者和用户
- 接受建设性的批评
- 关注对社区最有利的事情
- 表现出对其他社区成员的同理心

## 开始贡献

### 1. Fork 项目

点击项目页面右上角的 "Fork" 按钮，将项目 Fork 到你的 GitHub 账号下。

### 2. 克隆到本地

```bash
git clone https://github.com/YOUR_USERNAME/Infra-hub.git
cd Infra-hub

# 添加上游仓库
git remote add upstream https://github.com/Echo-Note/Infra-hub.git
```

### 3. 创建分支

```bash
# 从 dev 分支创建新分支
git checkout dev
git pull upstream dev
git checkout -b feature/your-feature-name
```

分支命名规范：
- `feature/xxx` - 新功能
- `bugfix/xxx` - Bug 修复
- `docs/xxx` - 文档更新
- `refactor/xxx` - 代码重构
- `test/xxx` - 测试相关

### 4. 开发环境配置

```bash
# 安装开发依赖
./setup-dev.sh

# 或手动安装
uv sync --dev
pre-commit install
```

### 5. 进行修改

在你的分支上进行代码修改，确保：

- 代码符合项目规范
- 添加必要的测试
- 更新相关文档
- 提交信息清晰明确

## 代码规范

### Python 代码风格

项目使用以下工具确保代码质量：

- **Black**：代码格式化（行长度 120）
- **isort**：import 语句排序
- **Flake8**：代码规范检查

所有代码提交前会自动通过 pre-commit 检查，你也可以手动运行：

```bash
# 运行所有检查
pre-commit run --all-files

# 只运行 black
pre-commit run black --all-files

# 只检查 staged 文件
pre-commit run
```

### 代码风格要点

1. **变量命名**
   - 类名使用 `PascalCase`
   - 函数和变量使用 `snake_case`
   - 常量使用 `UPPER_CASE`
   - 私有方法以 `_` 开头

2. **文档字符串**
   ```python
   def function_name(param1: str, param2: int) -> dict:
       """
       函数简短描述

       Args:
           param1: 参数1说明
           param2: 参数2说明

       Returns:
           dict: 返回值说明

       Raises:
           ValueError: 异常说明
       """
       pass
   ```

3. **类型提示**
   - 尽可能使用类型提示
   - 使用 Python 3.12+ 的新语法（如 `list[str]`）

4. **注释**
   - 使用中文注释
   - 复杂逻辑必须添加注释
   - 避免无意义的注释

### Django 规范

1. **模型设计**
   - 使用 `verbose_name` 和 `help_text`（中文）
   - 合理使用索引（`db_index=True`）
   - 重写 `__str__` 方法
   - 使用 `Meta` 类定义元数据

2. **视图开发**
   - 优先使用 ViewSet
   - 正确处理异常
   - 添加权限检查
   - 使用序列化器验证数据

3. **API 设计**
   - 遵循 RESTful 规范
   - 使用合适的 HTTP 方法
   - 返回统一的响应格式
   - 添加 API 文档

## 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建工具或辅助工具的变动

**示例**：

```
feat(virt_center): 添加虚拟机克隆功能

- 实现 VM 克隆 API 接口
- 添加克隆任务队列
- 支持自定义克隆配置

Closes #123
```

```
fix(vsphere_client): 修复连接超时问题

修复在网络不稳定时 vSphere 连接超时的问题，
增加重试机制和超时配置。

Fixes #456
```

### Commit 最佳实践

1. **提交频率**
   - 小步提交，每个提交只做一件事
   - 确保每次提交代码都可以运行
   - 避免提交大量无关文件

2. **提交内容**
   - 不要提交调试代码
   - 不要提交敏感信息（密码、密钥）
   - 不要提交编译产物和临时文件

3. **提交前检查**
   ```bash
   # 查看修改内容
   git diff

   # 查看将要提交的文件
   git status

   # 运行测试
   python manage.py test

   # 运行 pre-commit 检查
   pre-commit run --all-files
   ```

## 测试

### 编写测试

```python
from django.test import TestCase
from apps.virt_center.models import Platform

class PlatformTestCase(TestCase):
    """平台模型测试"""

    def setUp(self):
        """测试前准备"""
        self.platform = Platform.objects.create(
            name="测试平台",
            platform_type=Platform.PlatformType.VCENTER,
            host="10.10.100.20",
            port=443,
        )

    def test_platform_creation(self):
        """测试平台创建"""
        self.assertEqual(self.platform.name, "测试平台")
        self.assertTrue(self.platform.is_active)

    def test_connection_url(self):
        """测试连接 URL 生成"""
        expected_url = "https://10.10.100.20:443"
        self.assertEqual(self.platform.connection_url, expected_url)
```

### 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行指定应用的测试
python manage.py test apps.virt_center

# 运行指定测试类
python manage.py test apps.virt_center.tests.PlatformTestCase

# 显示详细输出
python manage.py test --verbosity=2
```

## 提交 Pull Request

### 1. 推送到 GitHub

```bash
# 提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送到你的 Fork
git push origin feature/your-feature-name
```

### 2. 创建 Pull Request

1. 访问你 Fork 的项目页面
2. 点击 "Pull Request" 按钮
3. 选择 `Echo-Note/Infra-hub` 的 `dev` 分支作为目标分支
4. 填写 PR 标题和描述

### 3. PR 描述模板

```markdown
## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化

## 变更说明
<!-- 描述你的更改内容 -->

## 相关 Issue
<!-- 如果有关联的 Issue，请在此列出 -->
Closes #123

## 测试说明
<!-- 描述如何测试这些更改 -->

## 检查清单
- [ ] 代码通过所有 pre-commit 检查
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 通过了所有单元测试
```

### 4. PR 审查流程

1. **自动检查**
   - CI/CD 会自动运行测试
   - pre-commit 会检查代码规范
   - 确保所有检查通过

2. **代码审查**
   - 维护者会审查你的代码
   - 可能会提出修改建议
   - 根据反馈进行调整

3. **合并**
   - 审查通过后会合并到主分支
   - 你的贡献会出现在项目中

## 报告 Bug

### Bug 报告模板

```markdown
## Bug 描述
<!-- 清晰简洁地描述 bug -->

## 复现步骤
1. 执行 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 期望行为
<!-- 描述你期望发生什么 -->

## 实际行为
<!-- 描述实际发生了什么 -->

## 环境信息
- OS: [e.g. Ubuntu 22.04]
- Python 版本: [e.g. 3.12.1]
- Django 版本: [e.g. 5.2.7]
- vSphere 版本: [e.g. 7.0]

## 截图
<!-- 如果适用，添加截图 -->

## 额外信息
<!-- 其他可能有用的信息 -->
```

## 功能建议

### 功能建议模板

```markdown
## 功能描述
<!-- 清晰简洁地描述你想要的功能 -->

## 使用场景
<!-- 描述这个功能将解决什么问题 -->

## 建议方案
<!-- 如果有，描述你的实现思路 -->

## 替代方案
<!-- 描述你考虑过的其他替代方案 -->

## 额外信息
<!-- 其他可能有用的信息 -->
```

## 文档贡献

文档同样重要！你可以：

- 修复文档中的错误
- 改进文档结构
- 添加使用示例
- 翻译文档

文档位于 `docs/` 目录，使用 Markdown 格式。

## 获取帮助

如果你在贡献过程中遇到问题：

1. 查看 [文档](README.md)
2. 搜索已有的 [Issues](https://github.com/Echo-Note/Infra-hub/issues)
3. 创建新的 Issue 寻求帮助
4. 加入讨论组交流

## 许可证

通过向本项目提交内容，你同意你的贡献将按照项目许可证进行授权。

---

再次感谢你的贡献！🎉
