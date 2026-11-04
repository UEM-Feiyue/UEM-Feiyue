# Engineering principles

1. Every line of code should justify its existence. Define once; reuse everywhere.
2. Keep the site static and accessible. Prefer HTML/CSS/vanilla JS. Add dependencies only when a real requirement justifies them.
3. Four editorial categories only: postgraduate exam, overseas study, employment, civil service/public institutions. Experiences include guidance; do not create a separate guide category.
4. `data/schema.json` owns category labels and submission fields. Never duplicate category definitions in multiple scripts.
5. No invented student stories, admission results, testimonials, or counts.
6. No hidden submission side effects. Never claim a submission succeeded until the backend confirms it.
7. Public GitHub Issues expose submitted content including optional contact details. Show a plain-language warning next to the form.
8. Use semantic markup, keyboard-accessible controls, responsive layouts, reduced-motion support, and readable contrast.
9. Changes should solve root causes, not accumulate patches. Prefer one coherent PR per engineering milestone, with tests before merging.
10. Commit messages record maintenance; PRs record meaningful engineering milestones.
