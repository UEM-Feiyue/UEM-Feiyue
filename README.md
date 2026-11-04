# UEM Feiyue · 应急管理大学飞跃手册

由同学共同维护的考研、留学、就业、考公考编经历分享站。

## 本地预览

```sh
python3 -m http.server 8000
```

访问 http://localhost:8000/ 。目前为第一阶段：静态界面、筛选、主题和投稿表单结构；尚未接入 GitHub Issue 投稿或发布工作流。不要将尚未接入的功能标记为已上线。

## 原则

- Every line of code should justify its existence.
- Define once. Reuse everywhere.
- 内容优先、原生优先、无前端构建依赖。
- 只保留四个方向；文章本身承载经验，不另设指南分类。
- 联系方式为可选项，投稿前提示 GitHub Issue 公开可见。
- 后续接入 Issue 审核时，只有 Close as completed 才触发发布，且需验证事件来源及内容。

## 结构

- `index.html`：首页与四个分类的统一入口
- `submit.html`：投稿界面（当前未启用实际提交）
- `assets/css/site.css`：全站样式
- `assets/js/site.js`：导航、主题、筛选
- `assets/js/submit.js`：投稿字段与预览
- `data/schema.json`：方向及表单字段的单一来源
- `data/articles.json`：文章索引（目前为空）
- `AGENTS.md`：维护约束

下一阶段：统一 Markdown 文章渲染和自动索引，再接入 Cloudflare Worker → GitHub Issue → 审核发布闭环。
