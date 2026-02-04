# Honda CALPHAD: Cu Removal from Recycled Steel

[![Open in Marimo](https://marimo.io/shield.svg)](https://molab.marimo.io/notebooks/nb_ZnGGazDX6TcpFZz6w9yaw3/app)

**MSE 4381 Senior Design Project | The Ohio State University | Spring 2026**

## Overview

This project uses CALPHAD (CALculation of PHAse Diagrams) simulation to identify ceramic materials capable of removing copper contamination from recycled steel melts.

### The Problem

- Recycled automotive steel contains copper from wiring, motors, etc. (0.25-0.3 wt% Cu)
- Copper causes **hot shortness** (cracking during hot working) above 0.1%
- No satisfactory industrial-scale Cu removal method exists
- Current solution: dilute with virgin iron or DRI (expensive, unsustainable)

### Our Approach

1. **CALPHAD Thermodynamics** — Screen ceramic candidates (Al₂O₃, MgO, TiO₂, SiO₂) for Cu affinity
2. **Mechanism Analysis** — Understand how ceramics capture Cu (solid solution, spinel formation, adsorption)
3. **Experimental Validation** — Electric furnace experiments in Fontana Lab

## Interactive Notebooks

### 1. Preliminary Analysis (Approximations)
**Ellingham diagram with temperature slider — uses linearized thermodynamic data**

- [Run in browser (Molab)](https://molab.marimo.io/notebooks/nb_ZnGGazDX6TcpFZz6w9yaw3/app)
- Local: `marimo edit simulations/pycalphad/cu_ceramic_thermodynamics.py`

### 2. Cu-O System (Real CALPHAD Database)
**Proper pyCALPHAD calculations using NIMS/Schramm (2005) database**

- **Molab version** (no dependencies): `cu_o_visualization.py` — loads pre-computed CSV
- **Local version** (requires pyCALPHAD): `cu_o_pycalphad.py` — runs calculations live
- **Data generator**: `compute_cu_o_data.py` — pre-computes and saves to CSV
- Database: `databases/cuo.tdb` — Schramm et al. (2005), *J. Phase Equilibria and Diffusion*, 26(6), 605-612

> **Note:** Molab doesn't have pyCALPHAD installed, so we pre-compute data locally and the Molab notebook loads from CSV or uses embedded data.

### 3. TC-Python (Full CALPHAD — OSU Lab Only)
**Thermo-Calc calculations for Cu-Al-O ternary phase diagrams**

- Requires OSU lab machine with ThermoCalc 2025b
- See `simulations/tcpython/README.md` for workflow

## Project Structure

```
honda-calphad/
├── README.md                    # This file
├── DOCUMENTATION.pdf            # Code explanation for non-programmers
├── THERMOCALC_GUIDE.pdf         # Step-by-step TC workflow
│
├── simulations/
│   ├── pycalphad/               # Runs locally (Mac/Windows/Linux)
│   │   ├── databases/
│   │   │   └── cuo.tdb          # Cu-O database (NIMS/Schramm 2005)
│   │   ├── cu_ceramic_thermodynamics.py   # Preliminary analysis (approximations)
│   │   ├── cu_o_pycalphad.py    # Real pyCALPHAD (local only)
│   │   ├── cu_o_visualization.py # Molab-compatible (loads pre-computed data)
│   │   ├── compute_cu_o_data.py # Generates CSV from pyCALPHAD
│   │   ├── cu_ceramic_affinity.py
│   │   └── pycalphad_cu_fe_example.py
│   │
│   └── tcpython/                # Runs on OSU lab machines only
│       ├── README.md            # TC-Python workflow documentation
│       ├── run_on_lab.bat       # Helper script for Windows
│       └── cu_al_o_phase_stability.py   # Phase equilibrium calculations
│
├── data/
│   ├── pycalphad/               # Pre-computed pyCALPHAD results
│   │   └── cu_o_gibbs_energies.csv
│   ├── thermocalc/              # Manual TC GUI exports
│   │   ├── raw/
│   │   └── processed/
│   ├── tcpython/                # TC-Python script outputs
│   │   ├── raw/
│   │   └── processed/
│   └── literature/              # Reference data from papers
│
├── literature/                  # Papers and references
└── reports/                     # Deliverables
```

## Computation Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  LOCAL (Your Computer)                                          │
│  • Write scripts, analyze data, create plots                    │
│  • pyCALPHAD for quick checks (open-source databases)           │
│  • Marimo notebooks for visualization                           │
└─────────────────────────────────────────────────────────────────┘
                               ↕ git push/pull
┌─────────────────────────────────────────────────────────────────┐
│  OSU LAB MACHINE (Remote)                                       │
│  • TC-Python with full databases (TCOX, TCFE, TCCU)             │
│  • Commercial CALPHAD calculations                              │
│  • Export results to data/tcpython/                             │
└─────────────────────────────────────────────────────────────────┘
```

## Key Findings (Preliminary)

| Question | Answer |
|----------|--------|
| Can Cu reduce Al₂O₃, MgO, SiO₂, TiO₂? | **No** — Cu oxides are thermodynamically least stable |
| How does Al₂O₃ capture Cu? | Solid solution, spinel formation (CuAl₂O₄), surface adsorption |
| Does sulfide exchange work? | **Yes** — FeS + Cu → Cu₂S + Fe is favorable at steelmaking temps |

## Data Sources

| Data | Source | Location |
|------|--------|----------|
| Cu-O thermodynamics | Schramm et al. (2005), *J. Phase Equilib. Diff.* 26:605 | `databases/cuo.tdb` |
| Oxide ΔGf approximations | NIST-JANAF, Barin tables | Documented in `cu_ceramic_thermodynamics.py` |
| Cu-Al-O phases | Thermo-Calc TCOX14 database | TC-Python (OSU license) |

## Requirements

**For local notebooks (pyCALPHAD):**
```bash
pip install marimo pycalphad numpy matplotlib
```

**For TC-Python (OSU lab machines):**
- ThermoCalc 2025b installed
- Python: `C:\Program Files\Thermo-Calc\2025b\python\python.exe`
- OSU VPN or on-campus network

## Team

**Anthony DiMascio** — Lead, Computational Modeling

**Advisors:** Prof. Alan Luo, Dr. Jianyue Zhang
**Industry Partner:** Honda R&D

## References

1. Schramm et al. (2005) — Cu-O thermodynamic reassessment, *J. Phase Equilibria and Diffusion*, 26(6), 605-612
2. Daehn et al. (2019) — Cu removal from steel scrap, *Met. Trans. B*
3. Matsuo et al. (2000) — Cu/Sn removal via decarburization, *ISIJ Int.*
4. Kattner (2016) — CALPHAD method overview

## License

This project is part of coursework at The Ohio State University. Contact the team for collaboration inquiries.
