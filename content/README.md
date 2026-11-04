# 投稿文章

每篇文章使用一个 Markdown 文件，文件顶部填写 YAML 元数据。构建脚本自动生成文章页面与 `data/articles.json`。

```yaml
---
title: 我的经历标题
category: kaoyan
author: 昵称
year: "2026"
major: 专业（可选）
destination: 去向（可选）
contact: 邮箱或社交账号（可选，公开展示）
excerpt: 一句话摘要（可选）
tags:
  - 复试
---
这里写正文。
```

`category` 必须是 `data/schema.json` 中定义的分类之一。不要提交未经当事人许可的个人信息。文章中不接受直接嵌入的 HTML。

## 演示文章

演示文章使用 `demo: true`，统一存放在 `content/demo/`。真实投稿增加后可以直接删除此目录，构建会自动清理对应页面与索引。演示不代表真实经历。
