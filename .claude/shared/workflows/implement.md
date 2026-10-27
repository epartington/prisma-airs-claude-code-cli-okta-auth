# Implementation Workflow

> Generic and portable — project specifics live in [CLAUDE.md](../../../CLAUDE.md).
> Pairs with [base.md](../system/base.md), [plan-first.md](plan-first.md), [review.md](review.md).

Use this **only after a plan is approved** via [plan-first.md](plan-first.md).
Never implement without an approved plan.

---

## 1. Pre-Flight

- [ ] The plan was explicitly approved.
- [ ] No `UNKNOWN` items remain; all `ASSUMED` items are confirmed or documented.
- [ ] The rollback path is clear.
- [ ] Affected systems/environments are understood.

**STOP if** there's no plan, it wasn't approved, or impact is unclear.

---

## 2. Execute Exactly as Planned

- [ ] Follow the plan step by step; make ONLY the listed changes.
- [ ] Do NOT add scope, features, or "improvements"; do NOT refactor unrelated code.
- [ ] Match existing patterns and conventions in the files you touch.
- [ ] Never commit secrets — check the diff before staging.
- [ ] Respect every guardrail in [CLAUDE.md](../../../CLAUDE.md).

---

## 3. Verify Before Commit

- [ ] Run the project's linters / formatters / type checks.
- [ ] Run the relevant tests (and add/update tests when behavior changed).
- [ ] Validate config/infra changes with the appropriate dry-run or validate command.
- [ ] Confirm no secrets or unintended files are included.
- [ ] Confirm the result actually matches the plan's intent.

Use the exact commands documented in [CLAUDE.md](../../../CLAUDE.md); if none is specified,
use the ecosystem's standard tooling.

---

## 4. Commit

- [ ] Stage ONLY the files in the approved plan.
- [ ] Write a clear message explaining **why**, not just what.
- [ ] Re-check the staged diff for secrets and stray changes.

Suggested message format:

```text
<type>: <concise description>

- Specific change 1
- Specific change 2

Context: <issue/plan reference if applicable>
```

Types: `feat`, `fix`, `docs`, `config`, `ci`, `refactor`, `chore`.

**Commit or push only when the user explicitly asks.**

---

## 5. Pre-Push / Pre-Apply Safety

Before any action that leaves your machine (push, deploy, apply, release):

- [ ] Changes match the approved plan and are on the intended branch.
- [ ] You understand what this triggers and what it affects.
- [ ] Prerequisites exist in the target (access, secrets, dependencies).
- [ ] The rollback plan is ready.
- [ ] The user approved the action when it affects shared/production systems.

---

## 6. Post-Change Verification

- [ ] The automated pipeline (if any) started and succeeded.
- [ ] The target reached the expected state (services healthy, outputs correct).
- [ ] No errors in the relevant logs/events.

**If it fails:** diagnose from logs, follow the documented rollback, and do NOT push
additional "fixes" without a new approved plan.

---

## 7. Update Documentation

- [ ] Update docs when behavior, setup, or interfaces changed.
- [ ] Record any new assumptions, gotchas, or recovery steps.

---

## Never Skip Verification For

- Changes to shared or production-affecting config/infra.
- Dependency, version, or schema upgrades.
- Access-control, permission, or secret-handling changes.
- Anything that triggers an automated deploy, release, or migration.
