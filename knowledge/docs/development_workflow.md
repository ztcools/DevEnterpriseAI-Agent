# 团队开发流程规范

## 1. Git工作流程

### 1.1 分支管理
- **main**: 主分支，用于生产环境
- **develop**: 开发分支，整合所有功能
- **feature/***: 功能分支，开发新功能
- **bugfix/***: 修复分支，修复线上bug
- **hotfix/***: 紧急修复分支

### 1.2 分支创建流程
```bash
# 从develop分支创建功能分支
git checkout -b feature/user-auth develop

# 开发完成后合并到develop
git checkout develop
git merge --no-ff feature/user-auth
git push origin develop
```

### 1.3 提交规范
提交信息格式：
```
<类型>(<范围>): <描述>

[详细说明]
```

**类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具更新

**示例**:
```
feat(user): 添加用户登录功能

- 实现JWT认证
- 添加密码加密
- 完善登录API
```

## 2. 代码审查流程

### 2.1 Pull Request规范
1. PR标题清晰描述变更内容
2. 关联相关Issue
3. 提供测试结果
4. 至少需要1位Reviewer批准

### 2.2 Code Review检查项
- 代码符合编码规范
- 逻辑正确性
- 性能考虑
- 测试覆盖率
- 安全隐患

## 3. 发布流程

### 3.1 版本号规则
采用语义化版本控制（Semantic Versioning）：
- `MAJOR.MINOR.PATCH`
- MAJOR: 不兼容的API变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的bug修复

### 3.2 发布步骤
1. 更新版本号
2. 更新CHANGELOG
3. 创建Tag
4. 部署到测试环境
5. 测试通过后部署到生产环境

## 4. 环境管理

### 4.1 环境类型
- **开发环境**: 本地开发使用
- **测试环境**: 功能测试和集成测试
- **预生产环境**: 生产前验证
- **生产环境**: 线上运行环境

### 4.2 配置管理
- 使用环境变量管理敏感配置
- 禁止硬编码配置值
- 配置文件加入.gitignore

## 5. 问题追踪

### 5.1 Issue分类
- **Bug**: 功能缺陷
- **Feature**: 新功能需求
- **Improvement**: 改进建议
- **Question**: 问题咨询

### 5.2 Issue处理流程
1. 创建Issue描述问题
2. 分配给相关开发人员
3. 开发人员修复并关联PR
4. PR合并后关闭Issue

## 6. 代码质量

### 6.1 静态检查
- 使用flake8检查Python代码
- 使用clang-format检查C++代码
- CI自动运行检查

### 6.2 测试覆盖
- 单元测试覆盖率≥80%
- 关键路径必须有测试
- CI自动运行测试