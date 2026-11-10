# 投稿文章

每篇文章使用一个 Markdown 文件，文件顶部填写 YAML 元数据。构建脚本自动生成文章页面与 `data/articles.json`。

```yaml
---
category: kaoyan
schema_version: 2
author: 昵称
year: "2026"
college: 学院
major: 专业
destination: 最终去向
institution_id: bit # 可空；仅引用 data/institutions.json 中已核实的 ID
admission_year: "2026"
degree_type: academic # academic / professional / other
admission_method: exam # exam / recommendation / independent / other
program: 专业、项目或岗位（必填）
contact: 邮箱或社交账号（可选，公开展示）
excerpt: 一句话摘要（可选）
tags:
  - 复试
---
这里写正文。
```

`category` 必须是 `data/schema.json` 中定义的分类之一。不要提交未经当事人许可的个人信息。文章标题自动使用「去向 · 专业/项目/岗位」生成，署名另显示「昵称 · 毕业届次 · 学院 · 专业」，无须单独填写标题；正文从 Markdown 文件本体读取。文章中不接受直接嵌入的 HTML。

考研以外的文章不填写录取年份、学位类型、录取方式或招生单位 ID。未收录的考研招生单位保留 `destination`，将 `institution_id` 留空，审核时再核实目录。历史文章和已签名的 version 1 Issue 仍按旧协议读取；新投稿使用 version 2。招生单位标签从目录中的独立属性生成，不在文章中手动维护院校层次。

## 演示文章

演示文章使用 `demo: true`，统一存放在 `content/demo/`。真实投稿增加后可以直接删除此目录，构建会自动清理对应页面与索引。演示不代表真实经历。

演示库固定四篇，每个方向一篇完整的虚构示例。前台只显示简洁的「演示」标识，不暗示文章为真人投稿；删除 `content/demo/` 即可全部移除。

投稿表单的 `data/demo-submission.md` 是独立的纯正文写作示例。

## Markdown 渲染约定

正文在投稿编辑器预览与正式文章中使用相同的 `.article-body` 视觉样式。
浏览器通过 Marked + DOMPurify 生成即时预览，静态构建由
`scripts/markdown_render.py` 使用 Python-Markdown + Bleach 完成。
两条路径采用相同的安全策略：把作者输入的原始 HTML 转为纯文本，
保留 Markdown 的结构字符（尤其是引用语法 `>`），最终禁止可执行 HTML。

支持标题、引用、加粗、删除线、列表、任务列表、链接、表格及围栏代码块。
由于客户端和构建端使用不同解析器，复杂的非标准 Markdown 扩展不属于
严格等价性承诺；受支持语法的结构和样式由 Python 单元测试和浏览器回归测试共同约束。

维护渲染规则时，应同时核对 `assets/js/submit.js`、
`scripts/markdown_render.py` 与 `assets/css/site.css`，不要只在单侧增加特殊样式。
