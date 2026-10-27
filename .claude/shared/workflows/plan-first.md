# Plan-First Workflow

> Generic and portable — project specifics live in [CLAUDE.md](../../../CLAUDE.md).
> Pairs with [base.md](../system/base.md), [implement.md](implement.md), [review.md](review.md).

Use this **before making ANY change** to code, configuration, or infrastructure.
Produce a plan and get explicit approval before touching anything.

---

## 1. Understand the Request

- [ ] Restate the goal in clear, specific terms.
- [ ] Classify the change (code / config / infra / CI / docs / dependency / other).
- [ ] Identify what is affected: which files, systems, services, environments.
- [ ] Assess blast radius: is it local, shared, or production-facing? Reversible?
- [ ] Check the project guardrails in [CLAUDE.md](../../../CLAUDE.md) that apply here.

---

## 2. Investigate Current State

- [ ] Read every file the change will touch, plus the patterns around them.
- [ ] Check `git status` and recent history for context.
- [ ] Review the relevant docs/conventions for constraints.
- [ ] Identify existing patterns to follow (don't invent new ones needlessly).
- [ ] Confirm current behavior/state before assuming what to change.

---

## 3. Identify Knowledge Gaps

Tag every assumption with a confidence level:

- **VERIFIED** — confirmed by reading files or inspecting state.
- **ASSUMED** — a reasonable inference, not confirmed.
- **UNKNOWN** — missing information; must ask.

**Stop and ask if any of these is UNKNOWN:**

- What exactly will be affected, and is it shared/production?
- Will this trigger an automated action (deploy, release, migration)?
- Are the prerequisites (access, credentials, dependencies) in place?
- Is the change reversible, and what are the rollback steps?
- Should it be validated somewhere safe first?

---

## 4. Design the Solution

- [ ] List every file to be modified and the specific change to each.
- [ ] Note the affected systems/environments and the order of operations.
- [ ] Identify risks and their mitigations.
- [ ] Prefer the smallest change that fully solves the problem — no extra scope.
- [ ] Confirm the change respects the guardrails in [CLAUDE.md](../../../CLAUDE.md).

---

## 5. Present the Plan for Approval

The plan must include:

1. **What** — specific changes to specific files.
2. **Where** — affected systems/environments.
3. **Why** — the reason for the change.
4. **Risk** — what could go wrong.
5. **Verification** — how you'll confirm it works.
6. **Rollback** — how to undo it.
7. **Prerequisites** — what must exist before applying.

**Wait for explicit approval.** On "go ahead" / "yes" / "approved", move to
[implement.md](implement.md). If anything is still `ASSUMED` or `UNKNOWN`, resolve it first.

---

## Never Skip This Workflow For

- Changes to shared or production-affecting config/infra.
- Anything that triggers an automated deploy, release, or migration.
- Dependency, version, or schema upgrades.
- Access-control, permission, or secret-handling changes.
- Any irreversible or hard-to-reverse operation.
