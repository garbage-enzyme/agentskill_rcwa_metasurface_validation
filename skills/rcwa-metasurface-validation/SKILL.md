---
name: rcwa-metasurface-validation
description: RCWA metasurface validation guide. Use when running grcwa, edmundsj rcwa, or RETICOLO for periodic scattering; validating COMSOL FEM spectra; resolving competing resonance branches; or auditing RCWA geometry, polarization, convergence, and energy closure. Covers local environments/APIs, dispersive lossy materials, curved inclusions, common-baseline FEM/RCWA comparisons, progressive-order peak convergence, provenance-safe long runs, and visual mode-evidence handoff.
---

# RCWA 操作指南（grcwa 0.1.2 + rcwa 1.0.48 + RETICOLO V10/V7）

本指南教你用 `grcwa`、`rcwa`（Python）和 `RETICOLO`（MATLAB）做周期散射、
长作业和 FEM/RCWA 交叉验证。先发现并记录当前主机的实际版本和路径；不要把下面
的已验证 Windows 路径当成其他用户或主机的默认值。

## 环境速查（本机实测）

### Python / grcwa / rcwa

| 项目 | 值 |
|------|-----|
| conda env | `comsol-mcp`：`D:\condaenvs\comsol-mcp\python.exe` |
| grcwa 版本 | 0.1.2（`pip install grcwa`） |
| rcwa (edmundsj) | 1.0.48（`pip install rcwa`） |
| 依赖 | numpy, autograd 1.9.1, scipy, matplotlib |
| pip index | `https://pypi.tuna.tsinghua.edu.cn/simple`（清华镜像） |

```powershell
& "D:\condaenvs\comsol-mcp\python.exe" -m pip install grcwa rcwa
```

验证：
```powershell
& "D:\condaenvs\comsol-mcp\python.exe" -c "import grcwa; print(grcwa.__version__)"
```

### MATLAB / RETICOLO

| 项目 | 值 |
|------|-----|
| MATLAB（2026-07-15 实测） | `25.2.0.3177638 (R2025b) Update 5`, `win64` |
| MATLAB 路径 | `D:\Program Files\MATLAB\R2025b\bin\matlab.exe` |
| 旧版备选 | R2021a：`D:\Program Files\Polyspace\R2021a\bin\matlab.exe` |
| RETICOLO V10（当前生产） | `D:\RETICOLO V10\V10_2025\reticolo_allege_v10`（148 个 `.m`） |
| RETICOLO V7（旧版） | `D:\reticolo_v7\reticolo_allege`（144 个 `.m`） |
| V10 文档 | `D:\RETICOLO V10\V10_2025\Documentation RETICOLO 2025.pdf` |
| V10 来源 | Zenodo `10.5281/zenodo.14631951`（RETICOLO 2025） |

本机生产路径：
```matlab
addpath('D:\RETICOLO V10\V10_2025\reticolo_allege_v10');
```

在其他主机上先用 `which res0 -all`、`which retio -all` 和 `version` 记录实际身份。
本机已有 V7 项目脚本可在 V10 下沿用基本 `res0/res1/res2` 调用，但每个新安装仍要做
一到三个已知点的兼容性门禁，不能仅凭目录名宣称兼容。

## RETICOLO 临时文件和内存安全

`retio(a,1)` 默认把超过 5000 个复数的变量写入当前目录下的 `retXXXX*.mat`。
高阶二维 RCWA 可快速产生大量临时文件。长作业必须先把工作目录放在有足够空间的
ASCII 路径，并显式选择以下策略之一：

```matlab
cd('D:\reticolo_scratch\job_name');

% Memory-resident strategy. Use only after RAM admission for the intended order.
[~, ~] = retio([], inf*1i);

% Always execute on normal exit and through onCleanup on errors.
retio;
```

- 内存足够且矩阵上界已知时，可用 `retio([], inf*1i)` 禁止临时矩阵写盘。
- 内存不足时保留写盘，但把 `cd` 指向大容量 scratch，并在每个独立点完成、结果落盘
  且不再需要 `aa/ef` 后调用 `retio` 清理本 session 临时文件。
- 不要等整段扫描结束才清理，也不要把 scratch 放在中文用户名路径或系统盘。
- 清理前必须先提取并持久化所需的 R/T/A 或场数据；`retio` 会同时清理内部缓存。
- 记录所用策略、scratch 路径、可用 RAM/磁盘门槛和 RETICOLO 版本。

## grcwa 0.1.2 API 速查

### 约定
- **自然单位**：真空介电常数=1，磁导率=1，光速=1。
- **时间约定**：`exp(-i*omega*t)`，与 COMSOL 一致。
- **频率**：`freq = 1/wavelength`（在 grcwa 约定下 c=1）。

### 核心类和方法

```python
import grcwa
import numpy as np

# 创建 RCWA 对象
obj = grcwa.obj(nG, L1, L2, freq, theta, phi, verbose=0)
# nG: 截断阶数（奇数=对称）
# L1, L2: 晶格矢量 [Lx, 0], [0, Ly]（单位 um）
# freq: 1/wavelength (c=1 约定)
# theta, phi: 入射角

# 添加均匀层
obj.Add_LayerUniform(thickness, eps)  # eps 可以是 float 或 complex

# 添加图案化层（网格）
obj.Add_LayerGrid(thickness, Nx, Ny)  # Nx*Ny 介电常数网格

# 最后一个 Add_LayerUniform(thickness=0, eps=substrate) = 半无限衬底
# 第一个 Add_LayerUniform(thickness=0, eps=air) = 半无限超衬底

# 初始化
obj.Init_Setup()

# 设置图案化层的介电常数
epgrid = np.ones((Nx, Ny), dtype=complex)
epgrid[patch_mask] = eps_patch  # complex permittivity
obj.GridLayer_geteps(epgrid.flatten())

# 平面波激励
obj.MakeExcitationPlanewire(p_amp, p_phase, s_amp, s_phase, order=0)

# 求解
R, T = obj.RT_Solve(normalize=1)
# R = 反射率, T = 透射率
# 吸收 A = 1 - R - T
```

### 关键陷阱

1. **Drude 介电常数**：grcwa 使用 `exp(-i*omega*t)` 约定，Lossy 材料写
   `eps = eps_inf - wp^2 / (omega*(omega - i*gamma))`。与 COMSOL 的 `-i*gamma` 约定一致。
   注意：`gamma` 必须为正数（正值=损耗）。

2. **介电常数必须是 complex 类型**：
   `epgrid = np.ones((Nx, Ny), dtype=complex)` — 否则 numpy 丢虚部。

3. **频率单位**：`freq = 1.0 / wl_um`（wavelength in um, c=1）。
   如果用 SI 频率需要 `freq = c / wl_m`，但 grcwa 约定 c=1，所以直接用 `1/wl`。

4. **半无限层**：`thickness=0` 表示半无限。第一个是超衬底（air），最后一个是衬底。

5. **能量守恒检查**：`A = 1 - R - T` 必须满足 `0 <= A <= 1` 且 `R + T <= 1`。
   如果 `R + T > 1`，增大 `nG`。

## grcwa vs rcwa vs RETICOLO 选择

| 工具 | 安装 | 负ε材料 | 2D图案化 | 速度 | 推荐场景 |
|------|------|---------|---------|------|---------|
| **grcwa** | `pip install grcwa` | ❌ 不支持 | ✅ 支持 | 快 | 普通介质光栅 |
| **rcwa** (edmundsj) | `pip install rcwa` | ⚠ 待验证 | ✅ 支持 | 中 | 金属/介质混合结构 |
| **RETICOLO V10/V7** | MATLAB addpath | ✅ 支持 (Li's因子化) | ✅ 支持 | 中 | 论文保真验证 |

**测试结论**（2026-07-11）：grcwa 对 In:CdO 在 5.5-6.6um（ε_real ≈ -10 to -16）产生 R>1 和 T<0，因 Laurent 展开无法处理金属/介质界面。`rcwa` 的 TMM(1,1) 对均匀叠层（air/Si3N4/In:CdO）给出正确 R 和能量守恒，待验证 2D 图案化层。

**推荐工作流**：
1. 先用 rcwa 做 TMM(1,1) 验证均匀叠层反射率
2. 再用 rcwa 的 2D RCWA 做图案化层，检查能量守恒
3. 如 rcwa 仍失败，用 RETICOLO（MATLAB）论文保真

## RETICOLO V10/V7 速查（MATLAB）

### 基本用法
```matlab
addpath('D:\RETICOLO V10\V10_2025\reticolo_allege_v10');
[~, ~] = retio([], inf*1i);  % only after memory admission

% Xu 2024 In:CdO MIM
LD = 5.8; D = [1, 1]; teta0 = 0; nh = 1; delta0 = 0;
parm = res0; parm.sym.x = 0; parm.sym.y = 0; parm.sym.pol = 1;
n_Si3N4 = sqrt(3.1329);
eps_incdo_ret = -11.46+1.25i;
n_incdo = sqrt(eps_incdo_ret);
if imag(n_incdo) < 0; n_incdo = -n_incdo; end

textures{1} = 1;              % 超衬底 air
textures{2} = n_incdo;        % 衬底 In:CdO
textures{3} = n_Si3N4;        % spacer
textures{4} = {1, [0,0,0.3,0.3, n_incdo, 1]};  % full patch dimensions

nn = [5, 5];
[aa, nef] = res1(LD, D, textures, nn, ro, delta0, parm);
profil = {[0, 0.1, 0.4, 0], [1, 4, 3, 2]};
ef = res2(aa, profil);
R = sum(ef.TEinc_top_reflected.efficiency);
T = sum(ef.TEinc_top_transmitted.efficiency);
A = 1 - R - T;
retio;
```

### 关键文件
- `reticolo.m` — 入口类（61 行，subsref 调度）
- `retcouche.m` — 层定义（44k 字符，核心）
- `retreseau.m` — 光栅/结构定义
- `retinc.m` — 入射场定义
- `retchamp.m` — 场计算（67k 字符）
- `exemple_general_2D.m` — 2D 光栅完整示例（10k 字符）
- `RETICOLO documentation.pdf` — 官方文档（1.3 MB）

## FEM vs RCWA 交叉验证工作流

### 步骤
1. **复用 COMSOL 的 Drude 参数**：从 FEM 脚本直接提取 `wp`、`gamma`、`eps_inf` 数值，避免符号不一致。
2. **按层定义 SCC 结构**：超衬底（air） → patch（图案化） → spacer（均匀） → substrate（半无限）。
3. **扫描相同波长范围**：与 FEM 相同的 `wl_start:wl_step:wl_end`，直接对比 CSV。
4. **能量守恒检查**：`A = 1 - R - T` 必须在 [0,1]，`R+T<=1`。
5. **模式分类**：如果 RCWA 只出单峰（论文结果），FEM 的长波分支是 FEM 伪影。如果 RCWA 也出双峰，论文可能遗漏了第二个模式。

### Xu 2024 In:CdO MIM 参数（n=1e20 cm^-3）

| 参数 | 值 | 来源 |
|------|-----|------|
| m_eff/m_e | 0.177996 | nonparabolic Option B |
| wp | 1.337168e+15 rad/s | precomputed |
| gamma | 2.410053e+13 rad/s | precomputed |
| eps_inf | 5.4 | Drude high-freq |
| eps(5.8um) | -11.46-1.25i | passive (Qh>0) |

结构（top→bottom）：
- Air（半无限超衬底）
- In:CdO patch in air（100nm, 300x300nm in 1x1um cell）
- Si3N4 spacer（400nm, eps=3.1329）
- In:CdO substrate（半无限，lossy）

COMSOL FEM 对比基准（0.0125*wl mesh）：
- MP1 @ 5.80 um, A_csc=0.918
- 长波分支 @ 5.925 um, A_csc=0.922
- Paper target @ ~5.75 um, A~0.836

### grcwa 脚本模板
`Desktop\pycode\Xu2024_InCdO_MIM\xu2024_rcwa_grcwa.py` — 完整的 grcwa 脚本，
预计算 Drude 参数、定义 4 层结构、扫描 5.5-6.6um、逐点 CSV 追加+flush+resume。

## 常见问题

### grcwa

1. **Q: nG 设多少？**
   A: 27 适合方形晶格 + 1 个图案化层。如果是高 Q 模式可能需要 51+。先跑 nG=11 做粗扫，再增大收敛。

2. **Q: R+T > 1 怎么办？**
   A: 增大 nG（截断阶数不够）。如果 nG=51 仍然不守恒，检查晶格矢量方向或介电常数符号。

3. **Q: 复介电常数怎么传？**
   A: `obj.Add_LayerUniform(thickness, complex(re, im))` 或直接 `obj.Add_LayerUniform(thickness, eps)` 其中 `eps` 是 Python `complex`。

4. **⚠ 已知限制：grcwa 不支持负介电常数（金属/等离子体）**
   Laurent Fourier factorization 在 ε 从正跳负时失效（R>1, T<0）。对 In:CdO (ε≈-11.5-1.25i)、Au、Ag 等金属材料不可用。换用 `rcwa`（edmundsj）或 RETICOLO。

### rcwa (edmundsj 1.0.48)

1. **`ur` 必须与 `er` 同尺寸传全网格**：`Crystal(er=er_grid, ur=ur_grid)` 中 `ur=1`（标量）会被
   `reshapeLowDimensionalData(1)` 展开为 `(1,1,1)`，导致谐波索引越界 (`index -2 out of bounds`)。  
   ✅ 正确用法：
   ```python
   ur_grid = np.ones((N, N), dtype=complex)
   crystal = rcwa.Crystal([P,0], [0,P], er=eps_grid, ur=ur_grid)
   ```

### RETICOLO

1. **Q: V10 还是 V7？**
   A: 新作业优先使用实际发现并通过已知点门禁的 V10；保留 V7 只用于旧结果复核。

2. **Q: 如何定义 material？**
   A: 参考 `exemple_general_2D.m` 和 `exemple_2D_pertes.m`（含损耗示例）。RETICOLO 用折射率 `n + i*k` 而非介电常数，注意 `eps = (n+ik)^2` 的转换。

## Cross-project RETICOLO audit rules

### Inclusion dimensions, curved shapes, and polarization

- RETICOLO inclusion vectors use full x/y dimensions, not half-widths or semiaxes:
  `[cx, cy, full_dx, full_dy, refractive_index, k]`.
- `k=1` is a rectangle. Larger `k` approximates an ellipse/circle with thin
  rectangles. Converge both `k` and Fourier order for curved high-Q structures.
- Put multiple inclusions in one patterned texture as
  `{background_index, inclusion_1, inclusion_2, ...}`. Swap full x/y dimensions for
  a 90-degree ellipse; do not invent a rotation property.
- At symmetry/normal incidence, solve `parm.sym.pol=1` and `-1` with separate
  `res1`/`res2` calls. Never read an unsolved polarization from the other result.
- At oblique incidence, match incidence plane, azimuth, and Bloch path; TE/TM names
  alone do not establish equivalence with COMSOL.

The Xu 2024 benchmark exposed the full-dimension trap: a 150 nm argument modeled the
wrong patch; the correct full 300 nm patch converged to `5.930 um, A=0.940` at
`nn=31`.

### Cell and order selection

- Prefer the smallest exact primitive/conventional cell. A doubled supercell folds
  bands, costs memory, and makes angular branch selection harder.
- For rectangular cells, equal x/y order counts do not give equal reciprocal-space
  coverage. Scale and converge the two directions independently.
- A bounded low-order spectrum can miss or shift a narrow resonance by many
  linewidths. Energy conservation is necessary, not modal convergence.

### Common-baseline contract for FEM/RCWA reconciliation

Before interpreting a peak offset, create a machine-readable audit table containing:

- source script/model path and SHA-256;
- lattice vectors and exact cell choice;
- full inclusion dimensions, centers, height, and curved-shape slices;
- every layer thickness and top/bottom termination;
- complex material values/expressions, units, wavelength convention, and passive sign;
- physical polarization, incidence direction, azimuth, and Bloch path;
- requested/evaluated wavelength, RCWA orders, and FEM mesh identity.

If any nominal input differs, create a named common working baseline and restart the
comparison. Do not explain a spectral difference before this gate passes.

### Progressive branch-aware convergence

1. Use low order only for geometry/sign/polarization smoke tests and approximate
   branch locations.
2. At the next order, evaluate a few wavelengths around every competing branch and
   recenter the bracket at that order's own maximum.
3. Run a narrow scan fine enough to bracket both sides and measure A and FWHM. Retain
   all local maxima, not only the global one.
4. Increase order progressively. Converge x/y orders and curved-shape slices
   independently when applicable.
5. Stop only when peak wavelength, A, and FWHM stabilize to declared tolerances.
   `R+T+A=1` proves closure, not modal convergence.
6. Compare FEM and RCWA at their own converged peaks on the common baseline. Treat a
   fixed-wavelength amplitude comparison as a diagnostic only.

A passive run with every requested row complete and every peak bracketed can
still fail the declared order-convergence gate. Report execution completion and
scientific acceptance separately. If peak wavelength, A, or FWHM remains outside
the gate at the declared order cap, preserve a diagnostic or residual status and
stop under reproduction scope unless the caller authorizes a larger convergence
campaign.

Before declaring that an angular branch disappears, run a bounded continuation
beyond the original wavelength window. A boundary maximum or weak response in
the old window proves only that the branch is unresolved there, not that it is
absent.

Prefer a few bracket points at the next order over a broad high-order scan. Never jump
to a very high order solely because a low-order scan lacks the FEM peak.

### Provenance-safe RCWA outputs

- Give every geometry/material/cell/polarization/order/slice configuration a stable
  `config_id` bound to the normalized configuration and source-script SHA-256; never
  mix configurations in one resumable CSV.
- Treat console-only or report-only peak/order claims as unverifiable. A summary may
  cite a configuration only when matching hash-bound raw rows exist for its exact
  `config_id`; otherwise exclude or quarantine the claim rather than reconstructing
  evidence from the summary.
- Append, flush, and `fsync` one wavelength row at a time. Resume only `ok` rows whose
  exact `config_id` matches; retry errors and partial rows.
- Record R/T/A, energy sum, order limits, slice count, cell choice, polarization,
  material convention, solve time, status, validation, and error.
- Mark scan-boundary maxima and failed energy/passivity rows explicitly. Exclude them
  from accepted peak fits and overlays.
- Agreement between two RETICOLO versions at identical configuration points validates
  backend compatibility for those points; it does not replace order convergence.
- Never run broad high-order RETICOLO beside a large standalone COMSOL solve. Sequence
  low-order smoke, progressive bracket points, narrow converged scan, then FEM overlay.

### Durable unattended MATLAB/RETICOLO runs

For jobs expected to run for hours:

1. Expose mode, angles/parameters, orders, output label, resume flag, scratch path, and
   wall limit through environment variables. Print the resolved configuration first.
2. Add a zero-solve `validate` mode that checks executable/toolbox paths, hashes,
   output headers, scratch writability, and the durable append primitive.
3. Run MATLAB `checkcode` and the `validate` mode before creating or approving a launcher.
4. Use a foreground PowerShell launcher that refuses MATLAB/COMSOL collisions, checks
   RAM, remaining commit, and scratch free space, writes a transcript, and lets the
   operator confirm before `matlab -batch "run('driver.m')"`.
5. Enforce the wall limit only between durable point rows. A 12 h limit means stop before
   starting the next point after 12 h; rerunning must resume exact completed identities.
6. Use both a launcher lock and a MATLAB-side lock. Remove a stale lock only after a fresh
   process inventory proves no owner exists.
7. Keep `onCleanup` objects alive for RETICOLO cleanup, directory restoration, locks, and
   Java file handles. MATLAB `R2025b Update 5` recognizes this lifetime use; obsolete
   `%#ok<NASGU>` suppressions can themselves produce `MSNU` messages.
8. For durable CSV append on Windows, `java.io.RandomAccessFile`, `getFD().sync()`, and
   close provide an explicit flushed point boundary. Publish summaries through a temp
   file plus atomic move.
9. If absorption is defined as `A=1-R-T`, label `R+T+A` as derived residual closure, not
   an independent absorption or power-closure measurement.

This pattern was zero-solve validated on MATLAB
`25.2.0.3177638 (R2025b) Update 5, win64`. It does not by itself validate any physics
point; run a bounded smoke solve before approving a new geometry for unattended work.

### Physical locator benchmark, not final convergence

For Sun 2024 nominal constant materials and finite Au, RETICOLO produced:

- `nn=9`: `5.418 um`, `A=0.7118`, FWHM about `16.36 nm`, `Q~331`;
- `nn=11`: `5.430 um`, `A=0.7153`, FWHM about `16.17 nm`, `Q~336`.

The 12 nm order shift makes this a physical locator, not a final result. It supports
the location/width of COMSOL's scattered-field candidate while rejecting its
unphysical `A=1.717` as emissivity evidence.

### Separate numerical export from visual classification

Wavelength and R/T/A agreement do not prove the same mode. Export matched field
components/slices and numerical component/on-off ratios where supported. A text-only
agent may generate standardized arrays and PNGs but must hand them to Codex or another
image-capable agent before claiming shared symmetry, localization, magnetic-dipole
character, or publication-ready overlay quality.
