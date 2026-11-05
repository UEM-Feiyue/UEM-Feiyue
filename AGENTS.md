# Engineering principles

1. Every line of code should justify its existence. Define once; reuse everywhere.
2. Keep the site static and accessible. Prefer HTML/CSS/vanilla JS. Add dependencies only when a real requirement justifies them.
3. Four editorial categories only: postgraduate exam, overseas study, employment, civil service/public institutions. Experiences include guidance; do not create a separate guide category.
4. `data/schema.json` owns category labels and submission fields. Never duplicate category definitions in multiple scripts. Article titles are derived from author, destination, and optional program; do not request a redundant title from contributors.
5. No invented student stories, admission results, testimonials, or counts.
6. No hidden submission side effects. Never claim a submission succeeded until the backend confirms it.
7. Public GitHub Issues expose submitted content including optional contact details. Show a plain-language warning next to the form.
8. Use semantic markup, keyboard-accessible controls, responsive layouts, reduced-motion support, and readable contrast.
9. Browser previews and published pages must use consistent Markdown structures and the shared `.article-body` CSS; any parser differences must be documented rather than hidden. Changes should solve root causes, not accumulate patches. Commit coherent milestones directly to main during the initial build phase; PRs are not required.
10. The emergency-blue palette is a custom interpretation until official UEM visual identity color values are verified.

11. Use `assets/icons/favicon.svg` for all browser favicons, `assets/images/favicon-横版.png` for shared header branding, and `assets/images/anguo-garden.jpg` as a restrained, top-only introductory background shared by all routes; fade the photo into the solid theme background before long-form content; never use a full-page/fixed photo behind reading areas; restore saved theme before stylesheet rendering with theme-init.js; generate HAI-inspired footer navigation from the homepage and schema; retain transparent content and no decorative hero widgets. Keep image references consistent on root and generated article pages.


## Project structure and development

- Root `index.html` and `submit.html` are directly editable UI sources. Keep `assets/`, `content/`, `data/`, `scripts/` and `tests/` organized by their actual project responsibilities. The independent Worker accepts public Issues only after explicit launch. The maintainer-only Completed closure importer owns reviewed Markdown publication; never bypass GitHub review.
- `preview.py` provides local preview and verified artifact replacement; `scripts/site_build.py` runs this project's content pipeline in isolation. Publish `_site/` only. Shared page chrome is drawn from the homepage during generation; do not add a separate framework merely to make this repository resemble another site.
- Schema owns required fields, limits and patterns. Keep the Worker fail-closed by default in version-controlled configuration and preserve the Cloudflare emergency kill switch. The public front-end config identifies the trusted endpoint and public Turnstile Site Key; production launch state is controlled by Cloudflare secrets and environment variables, never client-side security alone.
- Run `python -m unittest discover -s tests -t . -p 'test_*.py'`, `python preview.py --build-only` and `python tests/browser_smoke.py` for structural/UI changes. Each repository can evolve independently after this quality alignment.
- Treat cross-project alignment as a quality baseline, not a fixed repository template. Prefer familiar, purpose-driven organization; reuse proven logic only when it suits this project. Each site may evolve its UI, dependencies and structure independently.
