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

11. Use `assets/icons/favicon.svg` for all browser favicons, `assets/images/favicon-横版.png` for shared header branding, and `assets/images/anguo-garden.jpg` for the homepage's photographic hero only; preserve unified light/dark theme behavior on sidebar, hero, and article pages. Keep image references consistent on root and generated article pages.
