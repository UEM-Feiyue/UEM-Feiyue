# 开发与发布

在 Source 仓库根目录按任务选择命令：

**日常预览**：启动本地网站；修改源码后刷新浏览器，结束时按 Ctrl+C。

```sh
python preview.py
```

**提交前检查**：运行 Python 单元测试、Worker 安全测试，再构建完整静态网站。

```sh
python -m unittest discover -s tests -t . -p 'test_*.py' -v
node --test tests/worker.test.mjs
python preview.py --build-only
```

Windows 使用 `py -3` 替代 `python`；Worker 测试需要 Node.js 22+。预览默认在 `http://127.0.0.1:8765/`，`--build-only` 只验证并生成 `_site/`。**界面改动**还需运行 `python tests/browser_smoke.py`；PR 的 `validate.yml` 会运行浏览器检查。

## 发布与权限

Source 的 `deploy.yml` 在 `main` Push 后测试、构建 `_site/`，并用安装于 Source 和 Published 的 `UEM Feiyue Automation` App 将变化后的产物推送到 Published `main`。Source Actions 保存 Variable `PUBLISH_APP_ID` 与 Secret `PUBLISH_APP_PRIVATE_KEY`；缺少凭据会使发布失败，不会静默跳过。Published 的 Pages 从 `main` 根目录部署。通过 Published 的 `build-info.json` 核对源码提交和构建运行；产物未变化时不会生成新提交。

投稿 Worker 使用 UEM Feiyue Automation App 的 Source 范围短期 Issues token 创建 Source Issue，不使用个人令牌。它的生产开关位于 Cloudflare，见 `worker/README.md`。对应方向的审核 Team 成员或组织 Owner 以 Close as completed 审核有效投稿时，Source 的 `publish-completed-submission.yml` 验证 App 创建者、签名数据和审核身份，再用 App 提交 Markdown；Source Push 随后触发静态发布。Close as not planned 只清除待审标签，不生成内容。对真实投稿执行 completed 审核前应核对公开正文与联系信息。

不要把 App 私钥、Worker 凭据或 Turnstile 密钥提交进仓库。若旧 Published 中仍有待审核投稿，应先处理或迁移其审核记录，避免丢失待办。
