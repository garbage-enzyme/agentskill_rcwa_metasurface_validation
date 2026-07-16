# RCWA 超表面验证 — Agent Skill

[English](README.md) | 中文

教 AI 编码助手如何用 **RCWA（严格耦合波分析）** 验证 COMSOL FEM 的周期性超表面模拟结果。支持 `grcwa`（Python）和 `RETICOLO`（MATLAB）。

## 兼容工具：opencode、Claude Code、Codex 和 Hermes Agent

| 工具 | 入口文件 | 加载方式 |
| --- | --- | --- |
| **opencode** | `skills/rcwa-metasurface-validation/SKILL.md` | 从 `~/.config/opencode/skills/` 自动加载，任务匹配 frontmatter `description` 时触发 |
| **Claude Code** | `CLAUDE.md`（项目根） | `CLAUDE.md` 内含 `@skills/rcwa-metasurface-validation/SKILL.md`，import 语法把完整 skill 注入上下文 |
| **Codex CLI**（及任何读 AGENTS.md 的工具） | `AGENTS.md`（项目根） | `AGENTS.md` 被自动读取，指示 agent 在 RCWA 任务时打开 `skills/rcwa-metasurface-validation/SKILL.md` |
| **Hermes Agent** | `skills/rcwa-metasurface-validation/SKILL.md` | 安装到 `~/.hermes/skills/`，或通过 `skills.external_dirs` 暴露仓库的 `skills/` 目录 |

已依据 Hermes Agent 官方
[Skills System 文档](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md)
检查兼容性。本 skill 使用 Hermes 可扫描的 Agent Skills 结构：目录名与 frontmatter `name` 一致，包含必需的
`description`，且 `SKILL.md` 自包含。Hermes 专属 metadata 是可选项，因此不需要
维护 Hermes 专用分支。运行环境仍取决于主机：Hermes 选用的 terminal backend
必须能访问所需 Python 或 MATLAB/RETICOLO 安装，以及待比较的 FEM 证据。

唯一的内容源是 `skills/rcwa-metasurface-validation/SKILL.md`。`CLAUDE.md` 和 `AGENTS.md` 是薄指针，无内容重复。

## Skill 涵盖内容

- **grcwa 0.1.2 API**：`Add_LayerUniform`/`Add_LayerGrid`/`GridLayer_geteps`/`RT_Solve`，半无限衬底约定，复介电常数处理。
- **RETICOLO V10/V7**：MATLAB 配置、临时文件安全、耐久过夜 launcher，以及层/光栅/激励定义。
- **Drude 材料**：Python 预计算复 ε(ω)，符号约定与 COMSOL 的 `exp(-i*omega*t)` 一致。
- **grcwa vs FEM 交叉验证**：相同结构 → 对比 R/T/A 光谱；模式分类按场局域化。
- **平衡证据**：把 `A=1-R-T` 标为派生残差平衡并检查被动性；只有存在独立损耗量时才宣称独立能量闭合。

## 安装

### Option A — opencode

```powershell
git clone https://github.com/garbage-enzyme/agentskill_rcwa_metasurface_validation.git
Copy-Item -Recurse "agentskill_rcwa_metasurface_validation\skills\rcwa-metasurface-validation" "$env:USERPROFILE\.config\opencode\skills"
```

重启 opencode。RCWA 相关任务时会自动加载。

### Option B — Claude Code

在 `CLAUDE.md` 中添加：
```markdown
@/absolute/path/to/agentskill_rcwa_metasurface_validation/skills/rcwa-metasurface-validation/SKILL.md
```

### Option C — Codex CLI / AGENTS.md reader

在 `AGENTS.md` 中添加：
```markdown
For RCWA validation, read /absolute/path/to/agentskill_rcwa_metasurface_validation/skills/rcwa-metasurface-validation/SKILL.md first.
```

### Option D — 直接阅读

打开 `skills/rcwa-metasurface-validation/SKILL.md`。

### Option E — Hermes Agent

可直接从 GitHub 安装：

```bash
hermes skills install garbage-enzyme/agentskill_rcwa_metasurface_validation/skills/rcwa-metasurface-validation
```

也可以把完整 skill 目录复制到 `~/.hermes/skills/`，或在
`~/.hermes/config.yaml` 的 `skills.external_dirs` 中加入本仓库的 `skills/`
目录。

## 前提

- Python：`pip install grcwa`（numpy, autograd）
- MATLAB R2025b Update 5（已验证），或其他经过本机门禁的 MATLAB 版本
- 用于交叉验证的 COMSOL FEM 结果

## 仓库结构

```
.
├── skills/
│   └── rcwa-metasurface-validation/
│       └── SKILL.md           # 唯一内容源
├── scripts/
│   └── xu2024_rcwa_grcwa.py   # Xu 2024 In:CdO MIM 验证脚本
├── CLAUDE.md                   # Claude Code：@import
├── AGENTS.md                   # Codex / 其他：指针
├── README.md                   # this file (English)
├── README_CN.md                # 中文
└── LICENSE                     # MIT
```

## License

MIT — 见 [LICENSE](LICENSE)。
