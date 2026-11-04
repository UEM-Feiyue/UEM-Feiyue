# UEM Feiyue · 应急管理大学飞跃手册

由同学共同维护的考研、留学、就业、考公考编经历分享站。视觉以「应急蓝」为主，采用原创蓝色系设计变量（**非经校方确认的标准色值**）。

## 本地预览

```sh
python3 -m pip install -r requirements.txt
python3 scripts/build.py
python3 -m http.server 8000
```

访问 http://localhost:8000/ 。提交表单目前仅提供本地预览，**尚未连接 GitHub Issues**，不会真正投稿。

## 文章内容

Markdown 存于 `content/`，格式参见 `content/README.md`。运行 `scripts/build.py` 生成 `articles/*.html` 和 `data/articles.json`。当前不含虚构投稿。构建时依赖 Markdown、PyYAML 和 bleach；浏览器端不依赖前端框架。

## 部署

`main` 推送后，GitHub Actions 构建并发布到 GitHub Pages。需要在仓库 Settings → Pages 中将 Source 设置为 **GitHub Actions**。请以 Actions 的实际结果确认部署是否成功。

## 原则

- Every line of code should justify its existence.
- Define once. Reuse everywhere.
- 内容优先、原生优先、尽可能少的运行时依赖。
- 只保留四个方向；文章本身承载经验，不另设指南分类。
- 联系方式为可选项；未来 Issue 投稿会公开显示所有提交字段。
- 只有 Close as completed 才应触发后续自动发布，且需验证事件来源及内容。
