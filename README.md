# UEM Feiyue · 应急管理大学飞跃手册

由同学共同维护的考研、留学、就业、考公考编经历分享站。视觉以「应急蓝」为主，采用原创蓝色系设计变量（**非经校方确认的标准色值**）。

## 本地预览

```powershell
py -3 preview.py
```

macOS / Linux 使用 `python3 preview.py`。访问 <http://127.0.0.1:8765/>；保存内容后自动构建，刷新浏览器查看。仅构建使用 `py -3 preview.py --build-only`。初次运行会按需安装本项目依赖到 `.venv/`；不用额外启动源码目录服务器。

投稿表单保留预览与标签页草稿（联系方式不保存）。已实现独立 Cloudflare Worker → 公开 GitHub Issues → 维护者以 Close as completed 审核 → Markdown 自动发布链路。**公开投稿仍默认关闭**，须在验证端到端部署之后启用 `assets/js/submission-config.js` 的 `enabled` 开关与 Cloudflare Worker 公开模式；配置与操作见 [worker/README.md](worker/README.md)。

## 页面与内容

- 根目录 `index.html` 和 `submit.html` 直接维护首页与投稿界面。文章构建复用首页的导航、顶部栏和页脚，不需要维护额外模板目录。
- `content/` 保存 Markdown，格式见 [content/README.md](content/README.md)。演示文章继续明确标注，不代表真实投稿。
- `data/schema.json` 统一分类和字段规则；浏览器表单与 Python 构建都据此校验。扩展字段时先修改此处，再调整业务处理。
- `scripts/site_build.py` 在隔离目录中生成文章、列表和发布数据。文章列表、分类导航和页脚均在构建时输出；JavaScript 增强筛选和交互。
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

首页与分类列表在当前页面切换，地址和浏览器前进后退保持可用，筛选状态随历史记录恢复。文章与投稿保留独立页面；动画遵循系统的减少动态效果设置。
