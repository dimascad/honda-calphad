# Ellingham Diagram Data Extraction Process

## Honda CALPHAD Project | MSE 4381 Senior Design
**Date:** February 4, 2026
**Author:** Anthony DiMascio

---

## 1. Objective

Extract Gibbs energies of formation (ΔGf°) for oxide materials from Thermo-Calc's TCOX14 database to create an Ellingham diagram comparing oxide stability. This determines whether copper can thermodynamically reduce ceramic oxides (Al₂O₃, MgO, SiO₂, TiO₂) - a key question for the Cu removal project.

---

## 2. Background: What is an Ellingham Diagram?

An Ellingham diagram plots **ΔGf° per mole O₂** vs **temperature** for various metal oxide formation reactions.

**Key principles:**
- Lower (more negative) ΔG = more stable oxide
- A metal can reduce another metal's oxide only if its oxide line is BELOW the other
- The gap between lines indicates the thermodynamic driving force

**Our question:** Can Cu reduce Al₂O₃, MgO, SiO₂, or TiO₂?

---

## 3. Method Overview

### 3.1 Software and Database
- **Thermo-Calc 2025b** with **TC-Python** API
- **TCOX14** database (comprehensive oxide thermodynamics)
- Run on **OSU ETS Virtual Machine** (Windows, has Thermo-Calc license)

### 3.2 Oxides Calculated
| Oxide | Formula | Reaction (per mole O₂) |
|-------|---------|------------------------|
| Cuprite | Cu₂O | 4Cu + O₂ → 2Cu₂O |
| Tenorite | CuO | 2Cu + O₂ → 2CuO |
| Corundum | Al₂O₃ | 4/3Al + O₂ → 2/3Al₂O₃ |
| Periclase | MgO | 2Mg + O₂ → 2MgO |
| Quartz | SiO₂ | Si + O₂ → SiO₂ |
| Rutile | TiO₂ | Ti + O₂ → TiO₂ |
| Wüstite | FeO | 2Fe + O₂ → 2FeO |

### 3.3 Temperature Range
- 500 K to 2000 K
- 50 K intervals
- 31 data points per oxide

---

## 4. Calculation Details

### 4.1 Formation Energy Formula

For the reaction: Metal + O₂ → Oxide

$$\Delta G_f^{\circ} = G_{oxide}^{\circ} - n \cdot G_{metal}^{\circ} - G_{O_2}^{\circ}$$

Where:
- G°(oxide) = Gibbs energy of the oxide phase (per formula unit)
- G°(metal) = Gibbs energy of pure metal reference state
- G°(O₂) = Gibbs energy of O₂ gas at 1 atm
- n = stoichiometric coefficient

### 4.2 Normalization

All values normalized **per mole O₂** for Ellingham diagram comparison. For example:
- Cu₂O: multiply oxide coefficient by 2 (since 4Cu + O₂ → 2Cu₂O)
- Al₂O₃: multiply oxide coefficient by 2/3 (since 4/3Al + O₂ → 2/3Al₂O₃)

### 4.3 TC-Python Implementation

The script (`simulations/tcpython/extract_oxide_gibbs.py`) performs:

1. **O₂ Reference:** Calculate G(O₂) at each temperature using pure O system
   - GM returned is per mole O atoms → multiply by 2 for per mole O₂

2. **Metal Reference:** For each metal-oxygen system, calculate G(metal) at near-zero oxygen content (X_O = 0.0001)

3. **Oxide Phase:** Set stoichiometric composition and calculate equilibrium
   - Extract individual phase energy using `GM(PHASE_NAME)` (e.g., GM(CUPRITE#1))
   - Convert from per-atom to per-formula-unit by multiplying by atoms per formula

4. **Formation Energy:** Apply the ΔGf formula normalized per mole O₂

### 4.4 Key Technical Challenges Solved

**Problem 1: Two-phase equilibria**
- At stoichiometric oxide composition, TC sometimes finds two phases (e.g., CUPRITE + FCC_A1)
- **Solution:** Extract individual phase energy `GM(CUPRITE#1)` instead of system `GM`

**Problem 2: GM normalization**
- TC-Python returns GM per mole of atoms/sites, not per formula unit
- **Solution:** Multiply by atoms_per_formula (e.g., Cu₂O = 3 atoms)

**Problem 3: O₂ reference**
- GM for pure O is per mole O atoms, not O₂ molecules
- **Solution:** Multiply by 2 to get per mole O₂

---

## 5. Results

### 5.1 Data at 1000 K (727°C)

| Oxide | ΔGf° (kJ/mol O₂) | Phase Used |
|-------|------------------|------------|
| MgO | -986.8 | HALITE#1 |
| Al₂O₃ | -907.5 | CORUNDUM#1 |
| TiO₂ | -760.2 | RUTILE#1 |
| SiO₂ | -730.2 | QUARTZ#1 |
| FeO | -411.2 | HALITE#1 |
| Cu₂O | -190.8 | CUPRITE#1 |
| CuO | -132.0 | CUO#1 |

### 5.2 Key Finding

**Cu₂O is the LEAST stable oxide** with ΔGf° ~800 kJ/mol O₂ less negative than MgO or Al₂O₃.

This means Cu **cannot** reduce these ceramics:
$$\text{Cu} + \text{Al}_2\text{O}_3 \nrightarrow \text{Cu}_2\text{O} + \text{Al}$$

The thermodynamic driving force is massively unfavorable (~800 kJ/mol O₂ in wrong direction).

### 5.3 Physical Stability

Cu oxides also melt at lower temperatures than ceramics:
- Cu₂O melts at 1235°C (becomes IONIC_LIQ in TC)
- Al₂O₃ melts at 2072°C
- MgO melts at 2852°C

At steelmaking temperatures (1500-1600°C), Cu oxides are liquid while ceramic particles remain solid.

---

## 6. Implications for the Project

### What this tells us:
1. **Direct oxide reduction is impossible** - Cu cannot steal oxygen from Al₂O₃, MgO, SiO₂, or TiO₂
2. **Previous Cu capture observations** must involve different mechanisms

### Possible Cu removal mechanisms:
| Mechanism | Description |
|-----------|-------------|
| **Solid Solution** | Cu dissolves into oxide lattice (entropy-driven at high T) |
| **Spinel Formation** | CuO + Al₂O₃ → CuAl₂O₄ (requires Cu oxidation first) |
| **Surface Adsorption** | Cu adsorbs on ceramic particle surfaces |
| **Capillary Penetration** | Molten Cu wets porous ceramic structures |

### Next steps:
- Model Cu solubility in Al₂O₃ and MgO using Thermo-Calc
- Calculate CuAl₂O₄ spinel stability conditions
- Compare with last year's senior design experimental results

---

## 7. Files Generated

| File | Description |
|------|-------------|
| `data/tcpython/raw/oxide_gibbs_energies.csv` | Raw data (31 temps × 7 oxides) |
| `data/tcpython/ellingham_diagram_tcox14.png` | Static plot |
| `data/tcpython/ellingham_diagram_tcox14.pdf` | Vector plot for reports |
| `simulations/notebooks/ellingham_diagram.py` | Interactive Marimo notebook |
| `simulations/tcpython/extract_oxide_gibbs.py` | TC-Python extraction script |

### Interactive Notebook (Molab)
GitHub-synced link: Import from
`https://github.com/dimascad/honda-calphad/blob/main/simulations/notebooks/ellingham_diagram.py`

---

## 8. How to Reproduce

### On OSU ETS Virtual Machine:

```cmd
cd U:\4381\honda-calphad\simulations\tcpython
"C:\Program Files\Thermo-Calc\2025b\python\python.exe" extract_oxide_gibbs.py
```

Output goes to: `data/tcpython/raw/oxide_gibbs_energies.csv`

### To regenerate plots locally (Mac):

```bash
cd ~/School/Spring2026/MSE-4381-Capstone/honda-calphad
python3 -c "..." # (see data/tcpython/ for plotting script)
```

---

## 9. References

- Thermo-Calc TCOX14 Database Documentation
- Ellingham, H.J.T. (1944). "Reducibility of oxides and sulphides in metallurgical processes." J. Soc. Chem. Ind. 63: 125-133.
- Gaskell, D.R. "Introduction to the Thermodynamics of Materials" (standard MSE textbook)

---

*Document generated: February 4, 2026*
