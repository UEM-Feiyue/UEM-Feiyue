# UEM Feiyue · 应急管理大学飞跃手册

由同学共同维护的考研、留学、就业、考公考编经历分享站。视觉以「应急蓝」为主，采用原创蓝色系设计变量（**非经校方确认的标准色值**）。

## 本地预览

```powershell
py -3 preview.py
```

macOS / Linux 使用 `python3 preview.py`。访问 <http://127.0.0.1:8765/>；保存内容后自动构建，刷新浏览器查看。仅构建使用 `py -3 preview.py --build-only`。初次运行会按需安装本项目依赖到 `.venv/`；不用额外启动源码目录服务器。

投稿表单保留预览与标签页草稿（联系方式不保存）。已实现独立 Cloudflare Worker → 公开 GitHub Issues → 维护者以 Close as completed 审核 → Markdown 自动发布链路。站点公开投稿入口已接入独立 Turnstile 和 Worker；运行时由 Cloudflare `SUBMISSION_MODE` 与 `SUBMISSIONS_DISABLED` 控制，不能仅依赖前端开关。Cloudflare 验证、GitHub Issue 和 Close as completed 发布的维护说明见 [worker/README.md](worker/README.md)。

## 页面与内容

- 根目录 `index.html` 和 `submit.html` 直接维护首页与投稿界面。文章构建复用首页的导航、移动端菜单和页脚，不需要维护额外模板目录。
- `content/` 保存 Markdown，格式见 [content/README.md](content/README.md)。演示文章继续明确标注，不代表真实投稿。
- `data/schema.json` 统一分类和字段规则；浏览器表单与 Python 构建都据此校验。扩展字段时先修改此处，再调整业务处理。
- `scripts/site_build.py` 在隔离目录中生成文章、列表和公开数据，并使用与个人网页一致的 Pagefind 1.5.2 为 `_site/pagefind/` 生成静态全文索引。首页不维护第二套搜索文本：输入关键词时按需加载 Pagefind，文章结果仍可按方向和届次筛选。届次按钮采用紧凑的原生 Popover 增强选择菜单，旧浏览器保留 select 作为无障碍回退。
- `_site/` 是完整静态产物；只发布页面、资源和明确允许的公开数据，不上传源码根目录。

## 验证与部署

```sh
python3 -m unittest discover -s tests -t . -p 'test_*.py' -v
python3 preview.py --build-only
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
python3 tests/browser_smoke.py
```

`main` 推送后，GitHub Actions 构建并发布 `_site/`；Pages Source 应设为 GitHub Actions。Vercel 复用同一构建入口与目录。实际部署是否成功以对应平台结果为准。

## 原则

- Every line of code should justify its existence.
- Define once. Reuse everywhere.
- 内容优先、原生优先、尽可能少的运行时依赖。
- 只保留四个方向；文章本身承载经验，不另设指南分类。
- 联系方式为可选项；未来 Issue 投稿会公开显示所有提交字段。
- 只有 Close as completed 才应触发后续自动发布，且需验证事件来源及内容。

桌面端右侧从更高的自适应校园照片横幅直接开始，跟随系统／浅色／深色三态切换统一放在左侧导航底部；移动端在校园图片上方使用独立的 Logo 与菜单顶部栏，菜单浮层从顶部栏下方平滑展开。首页与分类列表在当前页面切换，地址和浏览器前进后退保持可用，筛选状态随历史记录恢复。文章与投稿保留独立页面；文章目录使用与投稿预览统一的可折叠目录和当前章节提示；投稿输入直接融入内容区，不另设大框。正文输入框随内容自动增长、支持手动拉高；「载入示例」仅加载源码并提供 Markdown 语法说明，不会强制跳转预览。联系方式仅提供公开渠道示例，不自动填入。动画遵循系统的减少动态效果设置。
