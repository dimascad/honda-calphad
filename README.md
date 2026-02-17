# Honda CALPHAD: Cu Removal from Recycled Steel

[![Open with marimo](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/https://github.com/dimascad/honda-calphad/blob/main/simulations/notebooks/ellingham_diagram.py)

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

## Interactive Ellingham Diagram

**[Open Interactive App](https://molab.marimo.io/https://github.com/dimascad/honda-calphad/blob/main/simulations/notebooks/ellingham_diagram.py)**

Real thermodynamic data from Thermo-Calc TCOX14 database — compare oxide stability with temperature slider.

**Local:** `marimo edit simulations/notebooks/ellingham_diagram.py`

## Key Findings

| Oxide | ΔGf° at 1000K (kJ/mol O₂) | Stability |
|-------|---------------------------|-----------|
| MgO | -986.8 | Most stable |
| Al₂O₃ | -907.5 | |
| TiO₂ | -760.2 | |
| SiO₂ | -730.2 | |
| FeO | -411.2 | |
| Cu₂O | -190.8 | |
| CuO | -132.0 | Least stable |

**Conclusion:** Cu₂O is ~800 kJ/mol O₂ less stable than MgO/Al₂O₃. **Cu cannot reduce these ceramics.** Any Cu removal mechanism must involve solid solution, spinel formation, or surface adsorption — not oxide reduction.

## Project Structure

```
honda-calphad/
├── README.md
├── docs/
│   ├── DOCUMENTATION.pdf         # Code explanation for non-programmers
│   ├── THERMOCALC_GUIDE.pdf      # Step-by-step TC workflow
│   └── ELLINGHAM_EXTRACTION_GUIDE.pdf  # How we extracted the data
│
├── simulations/
│   ├── notebooks/                # Marimo notebooks for visualization
│   │   ├── ellingham_diagram.py  # Main interactive diagram (TCOX14 data)
│   │   ├── databases/            # TDB files for pyCALPHAD
│   │   └── *.py                  # Other visualization notebooks
│   │
│   └── tcpython/                 # Runs on OSU lab machines only
│       ├── README.md
│       ├── extract_oxide_gibbs.py    # Main extraction script
│       └── check_databases.py        # Diagnostic script
│
├── data/
│   ├── tcpython/
│   │   ├── raw/oxide_gibbs_energies.csv  # Extracted Gibbs energies
│   │   ├── ellingham_diagram_tcox14.png
│   │   └── ellingham_diagram_tcox14.pdf
│   └── literature/               # Reference data from papers
│
└── reports/                      # Deliverables
```

## Computation Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  LOCAL (Your Computer)                                          │
│  • Analyze data, create plots                                   │
│  • Marimo notebooks for visualization                           │
│  • pyCALPHAD for quick checks (open-source databases)           │
└─────────────────────────────────────────────────────────────────┘
                               ↕ git push/pull
┌─────────────────────────────────────────────────────────────────┐
│  OSU LAB MACHINE (ETS Virtual Machine)                          │
│  • TC-Python with full databases (TCOX14, TCFE, TCCU)           │
│  • Commercial CALPHAD calculations                              │
│  • Export results to data/tcpython/                             │
└─────────────────────────────────────────────────────────────────┘
```

## Data Sources

| Data | Source | Status |
|------|--------|--------|
| Cu₂O, CuO, Al₂O₃, MgO, SiO₂, TiO₂, FeO | Thermo-Calc TCOX14 | ✅ Extracted |
| Cu-O TDB | Schramm et al. (2005) | ✅ Available |
| Fe-O TDB | NIMS (2011) | ✅ Available |
| Cu-Al-O ternary | TCOX14 | 🔜 Next step |

## Requirements

**For interactive notebooks:**
```bash
pip install marimo pandas numpy matplotlib
```

**For TC-Python (OSU lab machines):**
- ThermoCalc 2025b installed
- Python: `C:\Program Files\Thermo-Calc\2025b\python\python.exe`
- OSU ETS Virtual Machine access

## Team

**Anthony DiMascio** — Lead, Computational Modeling

**Advisors:** Prof. Alan Luo, Dr. Jianyue Zhang
**Industry Partner:** Honda R&D

## References

1. Thermo-Calc TCOX14 Database (2024)
2. Daehn et al. (2019) — Cu removal from steel scrap, *Met. Trans. B*
3. Ellingham, H.J.T. (1944) — Reducibility of oxides and sulphides, *J. Soc. Chem. Ind.*

## License

This project is part of coursework at The Ohio State University.
