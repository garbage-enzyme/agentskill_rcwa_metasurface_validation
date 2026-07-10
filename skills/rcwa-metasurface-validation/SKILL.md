---
name: rcwa-metasurface-validation
description: RCWA (Rigorous Coupled-Wave Analysis) metasurface validation environment. Use when running grcwa (Python) or RETICOLO (MATLAB) for periodic metasurface scattering validation of COMSOL FEM results. Covers grcwa 0.1.2 API (Add_LayerUniform/Add_LayerGrid/GridLayer_geteps/RT_Solve), RETICOLO V7 addpath setup, Drude material definition, energy conservation checks, and FEM vs RCWA cross-validation workflow for Xu 2024 In:CdO MIM.
---

# RCWA 操作指南（grcwa 0.1.2 + RETICOLO V7 + MATLAB R2025b）

本指南教你用 `grcwa`（Python）和 `RETICOLO`（MATLAB）做 RCWA 计算，验证 COMSOL FEM 结果。所有环境路径均经实测（2026-07-11）。

## 环境速查（本机实测）

### Python / grcwa

| 项目 | 值 |
|------|-----|
| conda env | `comsol-mcp`：`D:\condaenvs\comsol-mcp\python.exe` |
| grcwa 版本 | 0.1.2（`pip install grcwa`） |
| 依赖 | numpy, autograd 1.9.1 |
| pip index | `https://pypi.tuna.tsinghua.edu.cn/simple`（清华镜像） |

```powershell
& "D:\condaenvs\comsol-mcp\python.exe" -m pip install grcwa
```

验证：
```powershell
& "D:\condaenvs\comsol-mcp\python.exe" -c "import grcwa; print(grcwa.__version__)"
```

### MATLAB / RETICOLO

| 项目 | 值 |
|------|-----|
| MATLAB 版本 | R2025b Update 5：`D:\Program Files\MATLAB\R2025b\bin\matlab.exe` |
| 旧版 | R2021a：`D:\Program Files\Polyspace\R2021a\bin\matlab.exe`（备选） |
| RETICOLO 位置 | `C:\Users\陆星\Desktop\reticolo-blazr\RETICOLO V7`（含 ~200 个 .m 文件） |
| 来源 | GitHub: `awojdyla/reticolo-blazr`（含 RETICOLO V7 by IOGS） |

MATLAB 中使用 RETICOLO：
```matlab
addpath('C:\Users\陆星\Desktop\reticolo-blazr\RETICOLO V7');
```

注意：RETICOLO V7 的函数名以 `ret` 开头（如 `reticolo.m` 是入口类），大量辅助函数（`retcouche.m`、`retreseau.m` 等）。阅读 `exemple_general_2D.m` 了解完整 2D 用法。

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

## RETICOLO V7 速查（MATLAB）

### 基本用法
```matlab
addpath('C:\Users\陆星\Desktop\reticolo-blazr\RETICOLO V7');

% 定义光栅
n_layers = 4;
n_harmonics = 27;
lambda_min = 5.5; lambda_max = 6.5;

% 参考 exemple_general_2D.m 了解完整参数结构
% RETICOLO 使用 reticolo 类驱动计算
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

### RETICOLO

1. **Q: 版本兼容性？**
   A: RETICOLO V7 是 2018 左右的版本，在 R2021a 和 R2025b 上均可运行（纯 MATLAB 代码，无 MEX 依赖）。

2. **Q: 如何定义 material？**
   A: 参考 `exemple_general_2D.m` 和 `exemple_2D_pertes.m`（含损耗示例）。RETICOLO 用折射率 `n + i*k` 而非介电常数，注意 `eps = (n+ik)^2` 的转换。