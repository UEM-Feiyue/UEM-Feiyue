# UEM-Feiyue.github.io

> [!WARNING]
> 本仓库是自动生成的静态网站发布仓库。请勿直接修改文件：后续自动发布可能覆盖手动更改。

网站源码、文章、投稿审核、构建脚本与发布配置统一维护在 [UEM-Feiyue](https://github.com/UEM-Feiyue/UEM-Feiyue)。

Source 的 GitHub Actions 生成唯一的 `_site/` 静态产物，并在文件发生变化时通过 [**UEM Feiyue Automation**](https://github.com/apps/uem-feiyue-automation) GitHub App Bot 推送到本仓库 `main`。[GitHub Pages](https://uem-feiyue.github.io/) 直接部署这份产物，不在此重复构建。

`README.md` 由 Source 的 [PUBLISHED_README.md](https://github.com/UEM-Feiyue/UEM-Feiyue/blob/main/PUBLISHED_README.md) 生成；`build-info.json` 记录对应的源码提交和构建运行，供追溯与回滚。
