# 贡献指南

## 分支策略

- `main` — 稳定分支，**禁止直接提交**，只能通过 PR 合并
- `dev` — 开发分支，日常开发基于此分支
- `feat/xxx` — 功能分支，从 `dev` 创建
- `fix/xxx` — 修复分支，从 `dev` 或 `main` 创建

## 提交流程

1. 从 `dev` 创建功能分支: `git checkout -b feat/your-feature dev`
2. 完成开发后推送: `git push origin feat/your-feature`
3. 在 GitHub 创建 Pull Request，目标分支为 `dev`
4. 等待 CI 通过 + Code Review
5. 合并后删除功能分支

## Commit 规范

格式: `<type>: <描述>`

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `refactor` | 重构 |
| `docs` | 文档 |
| `test` | 测试 |
| `chore` | 构建/工具 |

示例:
```
feat: 添加用户注册接口
fix: 修复 SQL 注入漏洞
refactor: 重构 IoC 容器
```

## Pull Request 规范

- 标题清晰描述改动内容
- 说明改动的原因和背景
- 关联相关 Issue (如有)
- 确保 CI 通过
- 保持 PR 范围小，一个 PR 只做一件事

## 禁止事项

- 禁止直接向 `main` / `dev` 推送代码
- 禁止提交 `.env`、密钥等敏感文件
- 禁止提交 `.venv/`、`__pycache__/`、`*.db` 等生成文件
- 禁止使用 `git add .` 或 `git add -A`
