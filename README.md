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

## Quick Start

### Run the Interactive Notebook

**Option 1: Run locally with Marimo**
```bash
pip install marimo pycalphad numpy matplotlib
marimo edit simulations/pycalphad/cu_ceramic_thermodynamics.py
```

**Option 2: Run in browser (no install)**

[https://molab.marimo.io/notebooks/nb_ZnGGazDX6TcpFZz6w9yaw3/app](https://molab.marimo.io/notebooks/nb_ZnGGazDX6TcpFZz6w9yaw3/app)

### What's in the Notebook

- Interactive **Ellingham diagram** with temperature slider
- **Oxide stability rankings** that update dynamically
- **Sulfide exchange** thermodynamics (FeS + Cu → Cu₂S + Fe)
- Model **limitations** and recommended next steps

## Project Structure

```
honda-calphad/
├── README.md                 # This file
├── simulations/
│   └── pycalphad/
│       ├── cu_ceramic_thermodynamics.py   # Main Marimo notebook
│       ├── cu_ceramic_affinity.py         # Standalone analysis script
│       ├── pycalphad_cu_fe_example.py     # pyCALPHAD demo
│       └── *.png                          # Generated figures
├── literature/               # Papers and references
└── reports/                  # Deliverables
```

## Key Findings (Preliminary)

| Question | Answer |
|----------|--------|
| Can Cu reduce Al₂O₃, MgO, SiO₂, TiO₂? | **No** — Cu oxides are thermodynamically least stable |
| How does Al₂O₃ capture Cu? | Solid solution, spinel formation (CuAl₂O₄), surface adsorption |
| Does sulfide exchange work? | **Yes** — FeS + Cu → Cu₂S + Fe is favorable at steelmaking temps |

### Ellingham Diagram Summary

At 1600°C (typical steelmaking temperature):

| Oxide | ΔGf° (kJ/mol O₂) | Stability |
|-------|------------------|-----------|
| MgO   | -790 | Most stable |
| Al₂O₃ | -718 | |
| TiO₂  | -607 | |
| SiO₂  | -573 | |
| FeO   | -285 | |
| Cu₂O  | -59  | Least stable |

## Model Limitations

⚠️ **This is a simplified screening tool, not rigorous CALPHAD.**

The notebook uses linear ΔG = A + BT approximations from literature. For proper calculations:
- Use **Thermo-Calc** with TCOX/TCFE databases
- Model Cu solubility in oxide phases
- Calculate activity coefficients and phase diagrams

## Author

**Anthony DiMascio**

MSE 4381 Senior Design, The Ohio State University

**Advisors:** Prof. Alan Luo, Dr. Jianyue Zhang
**Industry Partner:** Honda R&D (Dr. Jim Hu)

## References

1. Daehn et al. (2019) — Cu removal from steel scrap, *Met. Trans. B*
2. Matsuo et al. (2000) — Cu/Sn removal via decarburization, *ISIJ Int.*
3. Kattner (2016) — CALPHAD method overview
4. Jung & van Ende (2020) — FactSage/CALPHAD simulation

## License

This project is part of coursework at The Ohio State University. Contact the team for collaboration inquiries.
