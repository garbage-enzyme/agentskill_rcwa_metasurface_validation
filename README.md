# RCWA Metasurface Validation — Agent Skill

English | [中文](README_CN.md)

An agent skill that teaches AI coding assistants how to validate periodic metasurface COMSOL FEM results using **RCWA (Rigorous Coupled-Wave Analysis)** — specifically `grcwa` (Python) and `RETICOLO` (MATLAB).

## Compatible with: opencode, Claude Code, Codex (and any AGENTS.md reader)

| Tool | Entry file it reads | How the skill loads |
| --- | --- | --- |
| **opencode** | `skills/rcwa-metasurface-validation/SKILL.md` | Auto-loaded from `~/.config/opencode/skills/` when the task matches the frontmatter `description` |
| **Claude Code** | `CLAUDE.md` (project root) | `CLAUDE.md` contains `@skills/rcwa-metasurface-validation/SKILL.md`, an import that injects the full skill body into context |
| **Codex CLI** / any AGENTS.md reader | `AGENTS.md` (project root) | `AGENTS.md` instructs the agent to open `skills/rcwa-metasurface-validation/SKILL.md` for RCWA tasks |

The single source of truth is `skills/rcwa-metasurface-validation/SKILL.md`. `CLAUDE.md` and `AGENTS.md` are thin pointers.

## What the skill covers

- **grcwa 0.1.2 API**: `Add_LayerUniform`/`Add_LayerGrid`/`GridLayer_geteps`/`RT_Solve`, semn-infinite substrate convention, complex permittivity handling.
- **RETICOLO V10/V7**: MATLAB setup, temporary-file safety, durable unattended launchers, and layer/grating/excitation definitions.
- **Drude material**: precompute complex ε(ω) in Python, sign convention matching COMSOL's `exp(-i*omega*t)`.
- **grcwa vs FEM cross-validation**: same structure → compare R/T/A spectra; mode classification by field localization.
- **Energy conservation**: `A=1-R-T` must close; `nG` truncation must be converged.

## Install

### Option A — opencode

```powershell
git clone https://github.com/garbage-enzyme/agentskill_rcwa_metasurface_validation.git
Copy-Item -Recurse "agentskill_rcwa_metasurface_validation\skills\rcwa-metasurface-validation" "$env:USERPROFILE\.config\opencode\skills"
```

Restart opencode. The skill will auto-load on RCWA tasks.

### Option B — Claude Code

Add to `CLAUDE.md`:
```markdown
@/absolute/path/to/agentskill_rcwa_metasurface_validation/skills/rcwa-metasurface-validation/SKILL.md
```

### Option C — Codex CLI / AGENTS.md reader

Add to `AGENTS.md`:
```markdown
For RCWA validation, read /absolute/path/to/agentskill_rcwa_metasurface_validation/skills/rcwa-metasurface-validation/SKILL.md first.
```

### Option D — read directly

Open `skills/rcwa-metasurface-validation/SKILL.md`.

## Prerequisites

- Python: `pip install grcwa` (numpy, autograd)
- MATLAB R2025b Update 5 (verified) or another locally validated MATLAB release for RETICOLO
- COMSOL FEM results for cross-validation

## Repository layout

```
.
├── skills/
│   └── rcwa-metasurface-validation/
│       └── SKILL.md           # single source of truth
├── scripts/
│   └── xu2024_rcwa_grcwa.py   # Xu 2024 In:CdO MIM validation script
├── CLAUDE.md                   # Claude Code: @import
├── AGENTS.md                   # Codex / any: pointer
├── README.md                   # this file (English)
├── README_CN.md                # 中文
└── LICENSE                     # MIT
```

## License

MIT — see [LICENSE](LICENSE).
