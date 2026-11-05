# UEM Feiyue submission Worker

This independent Cloudflare Worker accepts submissions from the production origin
`https://uem-feiyue.github.io` and creates **public GitHub Issues** in
`UEM-Feiyue/UEM-Feiyue.github.io`. It never edits published articles or bypasses
maintainer review.

## Configuration

- Worker name: `uem-feiyue-submissions`.
- API: `POST /submit`; public liveness endpoint: `GET /health`.
- Cloudflare Turnstile widget: restrict to `uem-feiyue.github.io`, action `uem_feiyue_submit`.
- Worker secrets: `GITHUB_TOKEN` and `TURNSTILE_SECRET`. Never commit their values.
- GitHub fine-grained PAT: restricted to this repository, **Issues: Read and write** only.
- Create the GitHub label `submission:pending` before enabling public submissions.
- The native rate limit binding is edge-local: three attempts per minute per IP, not a globally strict quota. The configuration's numeric namespace ID is local to this Worker; ensure it does not collide with another binding in the Cloudflare account.
- Allowlist the exact production origin only; no wildcard, no preview environment.

Run from `worker/` with Wrangler: `npx wrangler deploy`.
Before deployment, add secrets with
`npx wrangler secret put GITHUB_TOKEN` and
`npx wrangler secret put TURNSTILE_SECRET`.
The checked-in configuration is **closed by default**.
To launch, explicitly set both production variables to
`SUBMISSION_MODE=public` and `SUBMISSIONS_DISABLED=false` in the Cloudflare dashboard
*after* the secrets, origin, Turnstile, rate limiting and GitHub token have been verified.
Recheck the live settings after each deployment; the repository defaults remain closed.
To stop accepting submissions, change `SUBMISSIONS_DISABLED=true`.

## Contract and privacy

A JSON request has `version:1`, `category`, the fields from
`data/schema.json` (`author`, `year`, `destination`, `program`,
`body`, `contact`) and a `turnstileToken`. Validation uses the shared
schema, with a hard 64 KiB HTTP payload cap. The body and contact fields
also have explicit shared-schema length caps. No database or attachments.

Successful creation returns HTTP 201:
`{"ok":true,"issueUrl":"https://github.com/.../issues/123"}`.
A success response means **an Issue exists**, not that the story was approved
or published. Issues are public immediately, including any voluntarily
provided contact information. The Issue body includes an auditable
`uem-submission-v1` data marker for a future trusted publication importer.
Never publish directly from this untrusted Worker.

The submission UI has a public configuration in `assets/js/submission-config.js`,
including the public Site Key and Worker endpoint. Its `enabled` switch defaults
`false`; enable only after testing the live Worker and publication flow.
The trusted GitHub Actions importer in `scripts/import_completed_submission.py`
creates `content/community/issue-<number>.md` only for UEM submission Issues
closed **as completed by FuTseYi**. Ordinary closures, PRs, invalid markers,
other users and duplicate imports do not publish. A successful import pushes
Markdown to main, triggering the existing static site deployment. GitHub Actions
requires `contents: write` and repository workflow permission to push to main.
After rollout verify moderation, idempotency and page build using synthetic
Issues, and close test Issues as `not planned` to avoid publication.

## Security

Only permitted origins receive CORS headers. Every POST requires an explicit
open switch, a configured rate limiter, a bounded JSON body, server-side
Turnstile Siteverify (including hostname and action), and the GitHub token.
Any dependency failure rejects the request. No IP is placed into Issues.
An attacker can still abuse a public endpoint; monitor GitHub and Worker usage,
rotate credentials when necessary, and close the kill switch if abuse occurs.
