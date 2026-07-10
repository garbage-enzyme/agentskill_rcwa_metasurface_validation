# -*- coding: utf-8 -*-
"""RCWA validation of Xu 2024 In:CdO MIM using grcwa.

Structure (top to bottom):
  0. Air (semi-infinite superstrate)
  1. In:CdO patch in air (patterned, 100 nm thick, 300x300 nm in 1x1 um cell)
  2. Si3N4 spacer (uniform, 400 nm thick)
  3. In:CdO substrate (semi-infinite, lossy)

Cross-check against COMSOL FEM results:
  - FEM MP1 at 5.80 um, A_csc~0.918 (0.0125*wl mesh)
  - Paper target ~5.75 um, A~0.836
  - FEM long-wave branch: mesh-sensitive, not converged
"""
import csv
import math
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import grcwa

# ── Physical constants (SI) ──
C_SI = 2.99792458e8
HBAR = 1.054571817e-34
M_E = 9.1093837e-31
E_CHARGE = 1.602176634e-19
EPS0 = 8.8541878128e-12

# ── In:CdO Drude (Option B nonparabolic, m0_star=0.10*m_e) ──
N_CARRIER = 1.0e26
C_EV_INV = 0.69
C_J_INV = C_EV_INV / E_CHARGE
M0_STAR = 0.10 * M_E
M_EFF = M0_STAR * math.sqrt(
    1 + 2 * C_J_INV * HBAR**2 * (3 * math.pi**2 * N_CARRIER) ** (2 / 3) / M0_STAR
)
WP = math.sqrt(N_CARRIER * E_CHARGE**2 / (M_EFF * EPS0))
GAMMA = E_CHARGE / (410e-4 * M_EFF)
EPS_INF = 5.4

print(f"In:CdO: m_eff/m_e={M_EFF/M_E:.6f}, wp={WP:.6e}, gamma={GAMMA:.6e}")

# ── Geometry (um) ──
P = 1.0           # period
PATCH_L = 0.3     # patch lateral size
PATCH_H = 0.1     # patch height
D_SPACER = 0.4    # spacer thickness
EPS_SI3N4 = 3.1329

# ── RCWA parameters ──
nG = 27           # truncation order (odd = symmetric)
Nx = 200
Ny = 200

# ── Wavelength scan ──
wl_start = 5.5
wl_end = 6.6
wl_step = 0.025
wls = np.arange(wl_start, wl_end + wl_step / 2, wl_step)


def eps_incdo(wl_um):
    omega = 2 * math.pi * C_SI / (wl_um * 1e-6)
    return complex(EPS_INF - WP**2 / (omega * (omega - 1j * GAMMA)))


OUT_DIR = r"C:\Users\陆星\Desktop\iterations\Xu2024_InCdO_MIM"
CSV_PATH = os.path.join(OUT_DIR, "xu2024_rcwa_grcwa_n1e20.csv")
os.makedirs(OUT_DIR, exist_ok=True)

fields = ["wl_um", "nG", "Nx", "Ny", "R", "T", "A_1_RT", "A_1_R",
          "eps_re", "eps_im", "solve_time_s"]

# Resume
done = set()
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                done.add(round(float(row["wl_um"]), 9))
            except (KeyError, ValueError):
                pass

pending = [w for w in wls if round(float(w), 9) not in done]
print(f"wls: {len(wls)} total, {len(done)} done, {len(pending)} pending")
if not pending:
    print("all done")
    sys.exit(0)

write_header = not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0

# ── Pre-compute patch grid mask ──
x0 = np.linspace(0, 1, Nx, endpoint=False)
y0 = np.linspace(0, 1, Ny, endpoint=False)
x, y = np.meshgrid(x0, y0, indexing="ij")
PATCH_X0 = (P - PATCH_L) / P / 2  # fraction of unit cell
PATCH_FRAC = PATCH_L / P
patch_mask = (x >= PATCH_X0) & (x < PATCH_X0 + PATCH_FRAC) & \
             (y >= PATCH_X0) & (y < PATCH_X0 + PATCH_FRAC)

with open(CSV_PATH, "a", encoding="utf-8", newline="") as csvfile:
    w = csv.DictWriter(csvfile, fieldnames=fields)
    if write_header:
        w.writeheader()

    for i, wl in enumerate(pending, 1):
        t0 = time.time()
        eps_InCdO = eps_incdo(wl)
        freq = 1.0 / wl  # grcwa c=1 convention

        obj = grcwa.obj(nG, [P, 0], [0, P], freq, 0., 0., verbose=0)

        # Layer 0: air semi-infinite
        obj.Add_LayerUniform(0, 1.0)
        # Layer 1: patch (patterned)
        obj.Add_LayerGrid(PATCH_H, Nx, Ny)
        # Layer 2: Si3N4 spacer
        obj.Add_LayerUniform(D_SPACER, EPS_SI3N4)
        # Layer 3: In:CdO substrate semi-infinite
        obj.Add_LayerUniform(0, eps_InCdO)

        obj.Init_Setup()

        epgrid = np.ones((Nx, Ny), dtype=complex)
        epgrid[patch_mask] = eps_InCdO
        obj.GridLayer_geteps(epgrid.flatten())

        # S-polarization (TE), normal incidence
        obj.MakeExcitationPlanewave(0, 0, 1, 0, order=0)

        R, T = obj.RT_Solve(normalize=1)
        dt = time.time() - t0

        row = {
            "wl_um": f"{wl:.6f}",
            "nG": nG,
            "Nx": Nx,
            "Ny": Ny,
            "R": f"{R:.9f}",
            "T": f"{T:.9f}",
            "A_1_RT": f"{1 - R - T:.9f}",
            "A_1_R": f"{1 - R:.9f}",
            "eps_re": f"{eps_InCdO.real:.6f}",
            "eps_im": f"{eps_InCdO.imag:.6f}",
            "solve_time_s": f"{dt:.3f}",
        }
        w.writerow(row)
        csvfile.flush()
        os.fsync(csvfile.fileno())
        print(f"[{i:3d}/{len(pending)}] wl={wl:.3f} R={R:.6f} T={T:.6f} "
              f"A(1-RT)={1-R-T:.6f} A(1-R)={1-R:.6f} "
              f"eps={eps_InCdO.real:.2f}{eps_InCdO.imag:+.2f}i  t={dt:.2f}s",
              flush=True)

print(f"CSV: {CSV_PATH}")