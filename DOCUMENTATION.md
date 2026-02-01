# How This Works: A Non-Coder's Guide

## What We Built

An **interactive thermodynamic screening tool** that helps answer: "Which ceramic might best capture copper from molten steel?"

### The Files

| File | What it does |
|------|--------------|
| `cu_ceramic_thermodynamics.py` | Main interactive notebook (Marimo) - the one you share |
| `cu_ceramic_affinity.py` | Standalone script that generates the Ellingham diagram PNG |
| `pycalphad_cu_fe_example.py` | Demo showing how pyCALPHAD library works |
| `ellingham_diagram.png` | Static image of oxide stability comparison |
| `cu_fe_gibbs_energy.png` | Gibbs energy curves for Cu-Fe system |

---

## The Thermodynamics Explained

### 1. Gibbs Free Energy (ΔG)

This is the "will it react?" number:
- **ΔG < 0** → Reaction happens spontaneously (favorable)
- **ΔG > 0** → Reaction won't happen on its own (unfavorable)

### 2. How We Calculate It

For oxide formation, we use a simple linear approximation:

```
ΔGf° = A + B × T
```

Where:
- **A** = enthalpy part (kJ/mol) - roughly the "heat" of formation
- **B** = entropy part (kJ/mol·K) - how "disordered" things get
- **T** = temperature in Kelvin

Example for Cu₂O:
```
ΔGf°(Cu₂O) = -170 + 0.075 × T
```

At 1873 K (1600°C):
```
ΔGf° = -170 + 0.075 × 1873 = -170 + 140 = -30 kJ/mol
```

### 3. The Ellingham Diagram

To compare different oxides fairly, we normalize everything to "per mole of O₂":

| Oxide | Reaction | O₂ in reaction | Divide ΔGf by |
|-------|----------|----------------|---------------|
| Cu₂O | 2Cu + ½O₂ → Cu₂O | 0.5 mol | 0.5 |
| MgO | Mg + ½O₂ → MgO | 0.5 mol | 0.5 |
| Al₂O₃ | 2Al + 1.5O₂ → Al₂O₃ | 1.5 mol | 1.5 |
| SiO₂ | Si + O₂ → SiO₂ | 1.0 mol | 1.0 |

**Lower on the diagram = more stable oxide**

### 4. What the Diagram Tells Us

Cu₂O is at the TOP (least stable). This means:
- Cu **cannot steal oxygen** from Al₂O₃, MgO, SiO₂, or TiO₂
- The reaction Cu + Al₂O₃ → Cu₂O + Al will NOT happen
- We need a different mechanism to capture Cu

### 5. The Actual Mechanisms

Since Cu can't reduce the oxides, how does Al₂O₃ capture Cu? (It did in last year's experiments)

1. **Solid Solution** - Cu atoms dissolve into the ceramic crystal at high T
2. **Spinel Formation** - CuAl₂O₄ forms (requires Cu to oxidize first)
3. **Surface Adsorption** - Cu sticks to particle surfaces
4. **Capillary Action** - Molten Cu wets and penetrates porous ceramics

### 6. Sulfide Exchange (The Alternative)

Dr. Zhang showed this reaction works:
```
2Cu + FeS → Cu₂S + Fe
```

Why? Because Cu₂S is more stable than FeS (ΔG < 0 for this reaction).

---

## How the Code is Structured

### The Marimo Notebook Format

Marimo notebooks are Python files with special structure:

```python
import marimo
app = marimo.App()

@app.cell          # This decorator marks a "cell"
def _():
    # Code goes here
    return variables_to_share

@app.cell
def _(variables_from_above):
    # This cell can use those variables
    return more_variables
```

### Key Parts of Our Notebook

**1. Data Definition (oxide_data dictionary)**
```python
oxide_data = {
    'Cu₂O': (-170, 0.075, 0.5, '#0077BB', '-', '2Cu + ½O₂ → Cu₂O'),
    #        A      B     O2_factor  color  linestyle  reaction_string
}
```

**2. Calculation Functions**
```python
def calc_dGf_per_O2(name, T_K):
    A, B, O2_factor, *_ = oxide_data[name]
    return (A + B * T_K) / O2_factor
```

**3. Interactive Controls (Marimo UI)**
```python
temp_slider = mo.ui.slider(start=1000, stop=1700, value=1600)
oxide_selector = mo.ui.multiselect(options=[...], value=[...])
```

**4. The Plot**
- Creates matplotlib figure
- Loops through selected oxides
- Plots each line with its color/style
- Adds temperature marker and labels

---

## How to Make Changes

### Change the Temperature Range
Find this line and edit the numbers:
```python
temp_slider = mo.ui.slider(start=1000, stop=1700, ...)
```

### Add a New Oxide
Add an entry to `oxide_data`:
```python
'NewOxide': (A_value, B_value, O2_factor, '#HexColor', '-', 'Reaction string'),
```

Where:
- Look up A and B values from thermodynamic tables (NIST-JANAF, Barin)
- O2_factor = moles of O₂ in the formation reaction
- Color = hex code (use colorblind-friendly: #0077BB, #EE7733, #009988, #CC3311)

### Change Label Positions
Find the `_min_spacing` variable in the plot cell:
```python
_min_spacing = 45  # Increase this number for more space between labels
```

---

## Limitations (Important!)

This tool uses **simplified approximations**. It CANNOT:

| Limitation | Why it matters |
|------------|----------------|
| No activity coefficients | Real solutions aren't ideal |
| No phase diagrams | Can't find two-phase regions |
| No Cu solubility in oxides | This is the real mechanism! |
| No kinetics | Doesn't tell you how fast |
| Linear ΔG approximation | Real curves have more terms |

**For real CALPHAD calculations, you need Thermo-Calc with proper databases.**

---

## Next Steps: Thermo-Calc

### What Thermo-Calc Can Do That This Can't

1. **Proper phase diagrams** - Cu-Fe-O, Cu-Al-O ternary sections
2. **Cu solubility** - How much Cu dissolves in Al₂O₃ at 1600°C?
3. **Activity coefficients** - Real solution behavior
4. **Equilibrium calculations** - What phases are stable?

### Databases You Need

| Database | Contents | Use for |
|----------|----------|---------|
| TCFE | Steel thermodynamics | Cu in liquid Fe |
| TCOX | Oxide systems | Cu-Al-O, Cu-Mg-O |
| SSUB | Pure substances | Reference data |

### Calculations to Run in Thermo-Calc

1. **Cu-Fe binary phase diagram** - Understand Cu miscibility in Fe
2. **Cu activity in liquid Fe** - At 1600°C, how "active" is 0.3% Cu?
3. **Cu-Al-O isothermal section at 1600°C** - What phases form?
4. **Property diagram: Cu solubility in Al₂O₃ vs T** - The key data we need

### How to Transfer Results

1. Export Thermo-Calc data as CSV/TXT
2. We can import that into Python for visualization
3. Or add the validated values to this notebook

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────┐
│  This Notebook (Screening Tool)                         │
│  - Quick oxide stability comparison                     │
│  - Shows Cu CAN'T reduce these oxides                   │
│  - Identifies need for different mechanism              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Thermo-Calc (Rigorous CALPHAD)                         │
│  - Calculate Cu solubility in each oxide                │
│  - Model spinel formation conditions                    │
│  - Get real activity coefficients                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Experiments (Fontana Lab)                              │
│  - Test ceramics predicted to work best                 │
│  - Validate CALPHAD predictions                         │
│  - Measure actual Cu removal efficiency                 │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Reference: The Thermodynamic Data

### Oxide Parameters Used

| Oxide | A (kJ/mol) | B (kJ/mol·K) | O₂ factor | Source |
|-------|------------|--------------|-----------|--------|
| Cu₂O | -170 | 0.075 | 0.5 | NIST-JANAF (approx) |
| CuO | -155 | 0.085 | 0.5 | NIST-JANAF (approx) |
| FeO | -264 | 0.065 | 0.5 | NIST-JANAF (approx) |
| Al₂O₃ | -1676 | 0.32 | 1.5 | NIST-JANAF (approx) |
| MgO | -601 | 0.11 | 0.5 | NIST-JANAF (approx) |
| SiO₂ | -910 | 0.18 | 1.0 | NIST-JANAF (approx) |
| TiO₂ | -944 | 0.18 | 1.0 | NIST-JANAF (approx) |

### Sulfide Parameters

| Sulfide | ΔGf approximation | Source |
|---------|-------------------|--------|
| FeS | -150 + 0.027T | Literature estimate |
| Cu₂S | -180 + 0.032T | Literature estimate |

---

*Last updated: January 31, 2026*
