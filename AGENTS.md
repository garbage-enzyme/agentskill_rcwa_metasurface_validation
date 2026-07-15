# AGENTS.md — Codex / cross-tool entry point

This repository ships an **agent skill** for RCWA metasurface validation:

```text
skills/rcwa-metasurface-validation/SKILL.md
```

It is a focused instruction document (with YAML frontmatter) that teaches coding agents how to validate periodic metasurface COMSOL FEM results using grcwa (Python) and RETICOLO (MATLAB).

## When to read it

Read `skills/rcwa-metasurface-validation/SKILL.md` **before** running any RCWA validation task. The skill covers grcwa 0.1.2, rcwa 1.0.48, RETICOLO V10/V7, durable unattended MATLAB runs, Drude material conventions, and FEM vs RCWA cross-validation.

For the driving COMSOL agent skill, see https://github.com/garbage-enzyme/COMSOL_6_4_agentskill_for_metasurfaces
