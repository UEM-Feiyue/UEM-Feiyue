# 投稿文章

每篇文章使用一个 Markdown 文件，文件顶部填写 YAML 元数据。构建脚本自动生成文章页面与 `data/articles.json`。

```yaml
---
category: kaoyan
author: 昵称
year: "2026"
destination: 最终去向
program: 专业、项目或岗位（可选）
contact: 邮箱或社交账号（可选，公开展示）
excerpt: 一句话摘要（可选）
tags:
  - 复试
---
这里写正文。
```

`category` 必须是 `data/schema.json` 中定义的分类之一。不要提交未经当事人许可的个人信息。文章标题自动使用「署名 — 去向 · 专业/项目/岗位」生成，无须单独填写；正文从 Markdown 文件本体读取。文章中不接受直接嵌入的 HTML。

## 演示文章

演示文章使用 `demo: true`，统一存放在 `content/demo/`。真实投稿增加后可以直接删除此目录，构建会自动清理对应页面与索引。演示不代表真实经历。

演示库固定四篇，每个方向一篇完整的虚构示例。前台只显示简洁的「演示」标识，不暗示文章为真人投稿；删除 `content/demo/` 即可全部移除。

投稿表单的 `data/demo-submission.md` 是独立的纯正文写作示例。编辑器支持 CommonMark 与常见 GFM 排版；浏览器与 Python 发布使用不同解析器，复杂边界语法可能存在差异，公共语法及样式由测试约束。\n