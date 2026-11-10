# UEM Feiyue submission Worker

This independent Cloudflare Worker accepts submissions from the production origin
`https://uem-feiyue.github.io` and creates **public GitHub Issues** in
`UEM-Feiyue/UEM-Feiyue-Site-Source`. It never edits published articles or bypasses
maintainer review.

## Configuration

- Worker name: `uem-feiyue-submissions`.
- API: `POST /submit`; public liveness endpoint: `GET /health`.
- Cloudflare Turnstile widget: restrict to `uem-feiyue.github.io`, action `uem_feiyue_submit`.
- Worker secrets: `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`, `GITHUB_APP_PRIVATE_KEY` (PKCS#8 PEM), and `TURNSTILE_SECRET`. Never commit their values.
- The UEM Feiyue Site Automation App must be installed only on Source and Published, with Contents write, Issues write, and organization Members read. The Worker requests a Source-only, Issues-only installation token.
- Create the GitHub label `submission:pending` before enabling public submissions.
- The native rate limit binding is edge-local: three attempts per minute per IP, not a globally strict quota. The configuration's numeric namespace ID is local to this Worker; ensure it does not collide with another binding in the Cloudflare account.
- Allowlist the exact production origin only; no wildcard, no preview environment.

Run from `worker/` with Wrangler: `npx wrangler deploy`.
Before deployment, add secrets with
`npx wrangler secret put GITHUB_APP_ID`, `npx wrangler secret put GITHUB_APP_INSTALLATION_ID`, `npx wrangler secret put GITHUB_APP_PRIVATE_KEY`, and
`npx wrangler secret put TURNSTILE_SECRET`.
The checked-in configuration is **closed by default**.
To launch, explicitly set both production variables to
`SUBMISSION_MODE=public` and `SUBMISSIONS_DISABLED=false` in the Cloudflare dashboard
*after* the secrets, origin, Turnstile, rate limiting and GitHub token have been verified.
Recheck the live settings after each deployment; the repository defaults remain closed.
To stop accepting submissions, change `SUBMISSIONS_DISABLED=true`.

## Contract and privacy

A JSON request has `version:1`, `category`, the fields from
`data/schema.json` (`author`, `year`, `college`, `major`, `destination`, `program`,
`body`, `contact`) and a `turnstileToken`. Validation uses the shared
schema, with a hard 64 KiB HTTP payload cap. The body and contact fields
also have explicit shared-schema length caps. No database or attachments.

Successful creation returns HTTP 201:
`{"ok":true,"issueUrl":"https://github.com/.../issues/123"}`.
A success response means **an Issue exists**, not that the story was approved
or published. Issues are public immediately, including any voluntarily
provided contact information. The Issue body includes an auditable
`uem-submission-v2` data marker signed by the GitHub App key. The importer verifies this signature before trusting the category or content.
Never publish directly from this untrusted Worker.

The submission UI has a public configuration in `assets/js/submission-config.js`,
including the public Site Key and Worker endpoint. Its public `enabled` switch is `true` on the published site; production availability
still depends on Cloudflare `SUBMISSION_MODE=public` and `SUBMISSIONS_DISABLED=false`.
Do not treat the public browser switch as a security boundary.
The trusted GitHub Actions importer in `scripts/import_completed_submission.py`
creates `content/community/issue-<number>.md` only for App-created, signed UEM submission Issues
closed **as completed by a member of the signed category's review Team or an organization Owner** in Source. Ordinary closures, PRs, invalid markers,
unauthorized reviewers and duplicate imports do not publish. A successful import pushes
Markdown to main, triggering the existing static site deployment. GitHub Actions
requires `contents: write` and repository workflow permission to push to main.
  Use `not planned` for synthetic workflow checks; completed closures publish
  content publicly and should be reserved for reviewed real submissions.

## Security

Only permitted origins receive CORS headers. Every POST requires an explicit
open switch, a configured rate limiter, a bounded JSON body, server-side
Turnstile Siteverify (including hostname and action), and the GitHub App credentials.
Any dependency failure rejects the request. No IP is placed into Issues.
An attacker can still abuse a public endpoint; monitor GitHub and Worker usage,
rotate credentials when necessary, and close the kill switch if abuse occurs.
