# Review Workflow

> Generic and portable — project specifics live in [CLAUDE.md](../../../CLAUDE.md).
> Pairs with [base.md](../system/base.md), [plan-first.md](plan-first.md), [implement.md](implement.md).

Use this to review code, changes, or pull requests.

**READ-ONLY MODE: no edits, no implementations — analysis and recommendations only.**

---

## 1. Scope

- [ ] What is under review? (PR, commit, specific files, whole codebase.)
- [ ] What is the goal? (correctness, safety, quality, best practices.)
- [ ] What does it affect? (which systems/environments; is it production-facing?)

---

## 2. Safety & Security

- [ ] No secrets or credentials committed (in files or history).
- [ ] No sensitive files accidentally tracked (check `.gitignore` coverage).
- [ ] Access-control / permission changes follow least-privilege.
- [ ] Inputs are validated; no obvious injection or unsafe-handling paths.
- [ ] Guardrails in [CLAUDE.md](../../../CLAUDE.md) are respected.

---

## 3. Impact Analysis

- [ ] Does this trigger any automated action (deploy, release, migration)?
- [ ] Which systems/environments are affected, and is any production-facing?
- [ ] Is it reversible, and what is the rollback procedure?
- [ ] Are there breaking changes to interfaces, schemas, or contracts?

---

## 4. Correctness & Quality

- [ ] The change does what it claims and handles edge cases/errors.
- [ ] Syntax is valid; formatting and linting pass.
- [ ] Follows existing patterns and conventions; no unnecessary complexity.
- [ ] Tests cover the change and are meaningful.
- [ ] Changes are focused and coherent; no stray or unrelated edits.
- [ ] Commit messages are clear; docs are accurate and links aren't broken.

---

## 5. Risk Assessment

Rate the change:

- **LOW** — docs, comments, non-functional tweaks.
- **MEDIUM** — isolated config/code changes, dependency bumps (validated first).
- **HIGH** — shared/production changes, access-control or secret changes, schema/infra
  changes, anything that auto-deploys.

For **HIGH-risk** changes, confirm: validated safely first, rollback plan exists, the user
is aware of the impact, and existing behavior won't break.

---

## 6. Findings

Report in this structure:

- **Summary** — what was reviewed, what's affected, overall verdict
  (approve / needs changes / critical issues).
- **Critical (must fix)** — correctness, security, or breakage risks; each with what's
  wrong, why it matters, and how to fix.
- **Recommendations (should fix)** — reliability/maintainability improvements.
- **Observations (nice to have)** — minor or stylistic suggestions.
- **Questions** — anything unclear or needing verification.

---

## 7. Stop — Do Not Implement

- [ ] No edits, commits, or deployments.
- [ ] Report findings and await the user's decision.

If the user wants changes made: switch to [plan-first.md](plan-first.md), get plan approval,
then [implement.md](implement.md).

---

## Use This Workflow For

- Pre-commit and pull-request review.
- Security/correctness audits.
- "What could go wrong?" analysis before high-impact changes.
- Understanding existing behavior before modifying it.
