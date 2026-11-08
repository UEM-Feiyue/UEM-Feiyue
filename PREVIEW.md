# 开发与发布

在 Source 仓库根目录运行：

```sh
python preview.py
python -m unittest discover -s tests -t . -p 'test_*.py' -v
node --test tests/worker.test.mjs
python preview.py --build-only
```

Windows 使用 `py -3`。预览默认在 `http://127.0.0.1:8765/`，`--build-only` 只验证并生成 `_site/`。PR 的 `validate.yml` 还运行 Chromium/WebKit 浏览器检查。

## 生产切换

1. 为 UEM-Feiyue 安装可访问 Source 和 Published 的专用 GitHub App，授予这两个仓库 **Contents: Read and write**。在 Source Actions 中设置 Variable `PUBLISH_APP_ID` 和 Secret `PUBLISH_APP_PRIVATE_KEY`。发布工作流在变量缺失时跳过，避免误动生产仓库。
2. 确认 Source `main` 上的 `deploy.yml` 能通过测试并将 `_site/` 推送到 Published `main`；确认 Published Pages 从 `main` 根目录部署、产物页面与 `build-info.json` 对应同一次构建。
3. 在 Source 创建 `submission:pending`、`submission:published` 标签。更新 Cloudflare Worker 的 `GITHUB_TOKEN`，将其权限限定在 Source 的 **Issues: Read and write**；部署新的 Worker，并验证实际投稿 Issue 落在 Source。Worker 的生产开关由 Cloudflare 环境控制，详见 `worker/README.md`。
4. 验证维护者关闭测试 Issue 为 `not planned` 不发布；关闭合格 Issue 为 `completed` 后，Source 产生 Markdown 提交，Source 发布工作流再更新 Published。生产切换确认后，Published 仅保留生成文件。

不要把 App 私钥、Worker 凭据或 Turnstile 密钥提交进仓库。若旧 Published 中仍有待审核投稿，应先处理或迁移其审核记录，避免丢失待办。
