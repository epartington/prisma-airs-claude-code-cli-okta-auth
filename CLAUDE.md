# CLAUDE.md

Guidance for Claude Code (and humans) working in this repository.

## Working procedure

Before any change, Claude Code follows the generic workflows under
[`.claude/shared/`](.claude/shared/):

- [`.claude/shared/system/base.md`](.claude/shared/system/base.md) — base operating rules
  (plan first, never guess, never add scope, tag assumptions `VERIFIED`/`ASSUMED`/`UNKNOWN`).
- [`.claude/shared/workflows/plan-first.md`](.claude/shared/workflows/plan-first.md) — before
  any code/config/infra change: investigate, plan, get explicit approval.
- [`.claude/shared/workflows/implement.md`](.claude/shared/workflows/implement.md) — only
  after a plan is approved: execute, verify, commit only on explicit ask.
- [`.claude/shared/workflows/review.md`](.claude/shared/workflows/review.md) — read-only
  review/audit requests: no edits, findings only.

These files are generic and carry no project specifics. **This file (`CLAUDE.md`) wins on
any conflict** with them.

## Documentation style

All documentation — READMEs, this file, and inline code comments where applicable — must
follow Simplified Technical English (ASD-STE100). Before writing or editing
documentation, read
[`.claude/shared/output-styles/asd_ste100_style_guide.md`](.claude/shared/output-styles/asd_ste100_style_guide.md)
and apply its vocabulary, sentence-length, and active-voice rules. Check your own output
against the guide before finalizing it.

## What this project is

Configuration and tooling to authenticate the **Claude Code CLI** against a Prisma AIRS
AI Gateway (AIGW) deployment — self-hosted first, but the same setup applies to the
SaaS AIGW offering — using **Okta** as the OIDC identity provider. The gateway validates
the resulting **JWT bearer token** on inbound requests.

This repo holds two things:

- **Okta configuration instructions** — how to set up the Okta OIDC app (and any
  authorization server / API scopes) that the gateway trusts for bearer-token
  validation.
- **A helper script** that performs the Authorization Code + PKCE login against Okta,
  obtains a token, and makes it available for use with the gateway.

It is not an application with runtime business logic — it is auth plumbing and the docs
that explain how to set it up.

## Current state

- Early scaffolding. Only `README.md`, `CLAUDE.md`, `LICENSE`, and `.claude/` exist.
- The helper script and Okta setup docs have not been written yet.

## Auth flow

- **Flow:** Authorization Code with PKCE. The helper script opens the system browser
  for interactive login against Okta; no client secret is embedded in the script.
- **Script language:** Python, **standard library only** — no pip dependencies, so it
  runs on any machine with a stock Python 3 install.
- **Token caching:** the script caches the obtained credentials (access token, refresh
  token, expiry) locally and refreshes automatically when the access token is near
  expiry, so the browser/PKCE step only runs when there is no valid cached refresh
  token.
- **Token delivery to Claude Code CLI:** via the `apiKeyHelper` setting in Claude Code's
  settings. Claude Code runs the configured `apiKeyHelper` command whenever it needs a
  credential, and sends whatever that command prints to stdout as both the
  `Authorization: Bearer <token>` and `X-Api-Key: <token>` headers on requests to
  `ANTHROPIC_BASE_URL` (the gateway). So the helper script is the `apiKeyHelper`
  command: it must print a single valid access token to stdout (and only that — no
  extra output), refreshing or re-authenticating as needed before printing.

## Repository conventions

- Keep the Okta setup instructions and the helper script small and easy to verify —
  this is security-sensitive plumbing, not a demo app.
- Never commit secrets: Okta client IDs are fine to document, but client secrets
  (if ever needed), issued tokens, and cached credential files must never be committed.
  Add any local credential cache path to `.gitignore`.
- The helper script must not hardcode an Okta domain, client ID, or gateway URL —
  these are environment-specific and belong in environment variables or a local,
  gitignored config file, with documented examples/templates checked in instead.

## When writing the helper script

- Standard library only (e.g. `urllib`, `http.server` for the PKCE redirect listener,
  `json`, `secrets`/`hashlib` for the PKCE code verifier/challenge). No third-party
  packages.
- Keep the PKCE local redirect listener minimal and shut it down immediately after it
  receives the authorization code.
- Fail clearly and safely if the cached refresh token is invalid or expired — fall back
  to a fresh interactive PKCE login rather than silently erroring.

## Decisions log

Record notable choices here as they are made (Okta app settings, token delivery
mechanism, cache file location/format).

- **Flow:** Authorization Code + PKCE, via a standard-library-only Python helper
  script with local credential caching and automatic refresh.
- **Token delivery:** Claude Code's `apiKeyHelper` setting runs the helper script and
  uses its stdout as the bearer token / `X-Api-Key` sent to `ANTHROPIC_BASE_URL`. The
  script must print exactly one token to stdout and nothing else.
- **Open decisions (not yet made):** Okta authorization server and scope configuration;
  cached-credential file location and format; whether `apiKeyHelper` is set in user,
  project, or managed settings.
