# Ternary Reaction Analysis: Cu + MOx + O2 -> CuMOy

## Date: March 13, 2026
## Authors: Anthony DiMascio (MSE 4381 Capstone Team)
## Advisor: Dr. Jianyue Zhang

---

## 1. Background and Motivation

### Why Ternary Reactions?

Phase 1 of this project (Jan-Mar 2026) established that **copper cannot directly reduce
any useful ceramic oxide** at steelmaking temperatures. The Ellingham diagram shows Cu2O
is the least stable common oxide, with a ~200-1200 kJ/mol O2 gap between Cu2O and every
candidate ceramic. Direct reduction (Cu2O + MOx -> Cu + MOx+1) is thermodynamically
impossible for all 17 oxides screened.

However, Dr. Zhang identified that the actual Cu removal mechanism is not reduction but
**ternary compound formation**. When Al2O3 was tested experimentally (Year 2 of this
project), some copper was removed. The mechanism was CuAl2O4 spinel formation, not
Cu reduction of Al2O3. Zhang's directive (Mar 13 meeting):

> "We want to use the oxide to capture the copper inside."
> "If [dG] is negative, the reaction will happen."

### The Reaction

For each binary oxide MOx, we calculate:

    Cu + MOx + n*O2 -> CuMOy

where CuMOy is a ternary compound (spinel, vanadate, silicate, etc.) and n is determined
by stoichiometry. If dG_rxn < 0, the oxide can thermodynamically capture copper.

---

## 2. Method

### 2.1 TC-Python Extraction

**Script:** `simulations/tcpython/extract_ternary_reactions.py`
**Database:** TCOX14 (Thermo-Calc oxide database, 2025b)
**Temperature range:** 800-1900 K in 50 K steps (23 points per product)
**Systems:** 15 ternary Cu-M-O systems, 18 products total

For each product at each temperature:

1. Calculate G_Cu_metal: GM of pure Cu (FCC) from Cu-O system at X_O = 0.0001
2. Calculate G_O2: 2 x GM of pure O (gas phase) — converts per-atom to per-molecule
3. Calculate G_oxide_ref: GM of binary oxide at its stoichiometric composition,
   calculated WITHIN the ternary Cu-M-O system at X_Cu = 0.0001
4. Calculate GM_system: System Gibbs energy at the ternary compound composition
   (e.g., X_Cu = 1/7, X_Al = 2/7, X_O = 4/7 for CuAl2O4)

### 2.2 dG Calculation

    G_products = GM_system x atoms_per_formula
    G_reactants = n_Cu x G_Cu + n_oxide x oxide_atoms x G_oxide + n_O2 x G_O2
    dG_rxn = G_products - G_reactants

**Key**: GM from Thermo-Calc is per mole of ATOMS (intensive). We multiply by
atoms_per_formula to get the extensive Gibbs energy per formula unit of product.

### 2.3 Important Notes on the "System GM" Approach

This calculation uses the TOTAL SYSTEM Gibbs energy at the ternary composition, NOT the
Gibbs energy of a specific named phase. This means:

- TC finds whatever equilibrium phase assemblage is most stable at that composition
- If the system decomposes into multiple phases (e.g., CuO + RUTILE instead of CuTiO3),
  the GM still reflects the lowest-energy state
- A negative dG means the system at ternary composition is lower in energy than the
  separated reactants, REGARDLESS of whether a single ternary compound forms
- This is thermodynamically correct but means we cannot distinguish between
  "real compound formation" and "favorable mixing into an oxide melt"

---

## 3. Results

### 3.1 Summary: All 16 Reactions Favorable

Every modeled Cu + MOx + O2 -> CuMOy reaction has dG < 0 at all temperatures (800-1900 K).
At steelmaking temperature (1527C / 1800 K), dG ranges from -25.3 to -111.9 kJ/mol.

### 3.2 Ranked Results at 1527C (1800 K)

| Rank | Product    | dG (kJ) | Oxide | Type         | Named Phase  | Stable To  |
|------|-----------|---------|-------|--------------|-------------|------------|
| 1    | CuFe2O4   | -111.9  | FeO   | Spinel       | SPINEL#1    | 1700K      |
| 2    | Cu3V2O8   | -109.2  | V2O5  | Vanadate     | none        | --         |
| 3    | CuMn2O4   | -64.4   | MnO   | Spinel       | SPINEL#1    | 1700K      |
| 4    | Cu2SiO4   | -52.2   | SiO2  | Silicate     | none        | --         |
| 5    | CuB2O4    | -47.7   | B2O3  | Borate       | CUB2O4#1   | 1300K      |
| 6    | CuV2O6    | -45.0   | V2O5  | Vanadate     | none        | --         |
| 7    | CuTiO3    | -36.8   | TiO2  | Titanate     | none        | --         |
| 8    | CuCo2O4   | -35.8   | CoO   | Spinel       | SPINEL#1   | 1150K      |
| 9    | CuAl2O4   | -32.3   | Al2O3 | Spinel       | SPINEL#1   | 1550K      |
| 10   | CuCaO2    | -30.7   | CaO   | Hypothetical | none*       | --         |
| 11   | CuAlO2    | -30.1   | Al2O3 | Delafossite  | DELAFOSSITE | 1550K      |
| 12   | CuCr2O4   | -30.0   | Cr2O3 | Spinel       | SPINEL#1   | 1450K      |
| 13   | CuLaO2    | -27.8   | La2O3 | Compound     | DELAFOSSITE | 1500K      |
| 14   | CuNiO2    | -27.3   | NiO   | Compound     | none        | --         |
| 15   | CuSiO3    | -26.2   | SiO2  | Silicate     | none        | --         |
| 16   | CuMgO2    | -26.1   | MgO   | Hypothetical | none**      | --         |
| 17   | CuZrO3    | -25.3   | ZrO2  | Hypothetical | none        | --         |
| --   | CuCeO3    | N/A     | CeO2  | Hypothetical | CE not in DB| --         |

*TC found Ca2CuO3 (calcium cuprate) instead of CuCaO2
**TC found Cu2Mg2O5 (GUGGENITE) instead of CuMgO2

### 3.3 Two-Tier Structure

The results naturally divide into two groups:

**Strong tier (dG < -45 kJ):** CuFe2O4, Cu3V2O8, CuMn2O4, Cu2SiO4, CuB2O4, CuV2O6
- Large thermodynamic driving force
- Likely to overcome kinetic barriers at steelmaking temperatures
- Genuine compound formation or strong preferential dissolution

**Moderate tier (dG = -25 to -37 kJ):** CuTiO3, CuCo2O4, CuAl2O4, CuCaO2, CuAlO2,
CuCr2O4, CuLaO2, CuNiO2, CuSiO3, CuMgO2, CuZrO3
- dG is only ~2x kT at 1800 K (kT ~ 15 kJ/mol)
- Kinetic barriers may prevent reaction in practice
- May represent simple mixing into ionic liquid with no specific Cu-capturing mechanism

### 3.4 Per-Cu Normalization

Some reactions consume multiple Cu atoms. Normalizing per Cu:

| Product    | Total dG (kJ) | n_Cu | dG per Cu (kJ) |
|-----------|---------------|------|----------------|
| CuFe2O4   | -111.9        | 1    | -111.9         |
| Cu3V2O8   | -109.2        | 3    | -36.4          |
| CuMn2O4   | -64.4         | 1    | -64.4          |
| Cu2SiO4   | -52.2         | 2    | -26.1          |

CuFe2O4 is genuinely the most efficient per Cu atom. Cu3V2O8 drops significantly
when normalized — its total is large because it captures 3 Cu atoms at once,
but the per-Cu efficiency is only moderate.

---

## 4. Phase Stability Analysis

### 4.1 Key Finding: No Ternary Phase Survives at 1800 K

At steelmaking temperature (1527C / 1800 K), every named ternary compound has melted
into the ionic liquid phase (IONIC_LIQ). The system equilibrium at 1800 K is typically:
GAS + IONIC_LIQ (with or without a refractory binary oxide like CORUNDUM or ZRO2_TETR).

### 4.2 Phase Persistence by Product

Compounds with named ternary phases (7 of 18):

| Product   | Phase Name    | Stable Range | Melts At | High-T Replacement           |
|----------|--------------|-------------|---------|------------------------------|
| CuFe2O4  | SPINEL#1     | 800-1700 K  | ~1750 K | GAS + IONIC_LIQ              |
| CuMn2O4  | SPINEL#1     | 800-1700 K  | ~1750 K | GAS + IONIC_LIQ              |
| CuAl2O4  | SPINEL#1     | 800-1550 K  | ~1600 K | CORUNDUM + GAS + IONIC_LIQ   |
| CuAlO2   | DELAFOSSITE  | 800-1550 K  | ~1600 K | CORUNDUM + IONIC_LIQ x2      |
| CuLaO2   | DELAFOSSITE  | 800-1500 K  | ~1550 K | IONIC_LIQ x2 + M2O3A        |
| CuCr2O4  | SPINEL#1     | 800-1450 K  | ~1500 K | CORUNDUM + DELAFOSSITE + GAS |
| CuB2O4   | CUB2O4#1     | 800-1300 K  | ~1350 K | GAS + IONIC_LIQ              |
| CuCo2O4  | SPINEL#1     | 800-1150 K  | ~1200 K | HALITE + IONIC_LIQ + GAS     |

Compounds that NEVER show a named phase (10 of 18):
CuV2O6, Cu3V2O8, CuTiO3, CuSiO3, Cu2SiO4, CuMgO2, CuCaO2, CuZrO3, CuNiO2, CuCeO3

For these, TC always decomposes the system into binary oxides + Cu oxides + ionic liquid.
The negative dG reflects favorable mixing, not discrete compound formation.

### 4.3 Significance for Experiments

The fact that all compounds melt before steelmaking temperature has two implications:

**For the science:** At 1527C, copper capture is through DISSOLUTION INTO AN OXIDE SLAG,
not crystalline compound formation. The Cu dissolves into a molten oxide (IONIC_LIQ) phase.

**For experiments:** This may actually be ADVANTAGEOUS. A liquid slag has:
- Better contact with the molten steel (liquid-liquid interface vs. solid-liquid)
- Faster kinetics (no solid-state diffusion limitation)
- Easier separation (slag floats, can be skimmed)

The compounds that come closest to surviving at steelmaking temperature (CuFe2O4 and
CuMn2O4, both stable to 1427C) also have the strongest dG values. This correlation
makes physical sense: a compound with a large formation energy can resist decomposition
to higher temperatures.

### 4.4 Unexpected Phases Found by TC

For some "hypothetical" compounds, TC found REAL ternary phases that we did not
specifically target:

- **Cu-Ca-O system:** TC found **Ca2CuO3** (calcium cuprate) as a stable phase from
  800-1300 K. This is a known high-Tc superconductor parent compound. It may be relevant
  as an alternative Cu capture mechanism for CaO.

- **Cu-Mg-O system:** TC found **GUGGENITE (Cu2Mg2O5)** as a stable phase from
  1150-1350 K. This is a known mineral. The Cu-Mg-O system may capture Cu through
  this compound rather than the hypothetical CuMgO2.

- **Cu-Cr-O system:** After CuCr2O4 spinel decomposes at ~1500 K, TC finds
  **CuCrO2 (DELAFOSSITE)** as a stable phase. The Cr system may have TWO different
  Cu-capturing mechanisms at different temperatures.

---

## 5. Concerns and Caveats

### 5.1 Why Are ALL Reactions Favorable?

The fact that all 16 modeled reactions have dG < 0 deserves scrutiny. The "system GM"
approach compares the equilibrium state at a ternary composition to separated reactants.
Since TC always finds the lowest-energy state (including multi-phase equilibria and
liquid solutions), ANY mixing that lowers the energy — even simple dissolution with
no specific compound formation — gives dG < 0.

The moderate-tier results (-25 to -37 kJ) should be interpreted cautiously. These may
reflect generic oxide mixing rather than specific Cu-capturing reactions. The strong-tier
results (-45 to -112 kJ) are more likely to represent genuine compound formation or
strong preferential interactions.

### 5.2 CuFe2O4: The -112 kJ Is Misleading

CuFe2O4 (cuprospinel) IS a real compound — it has been synthesized and characterized
extensively. It adopts an inverse spinel structure (Fe3+ on tetrahedral sites, Cu2+ and
Fe3+ on octahedral sites). However, the -112 kJ value is misleading for our application.

**The Fe-oxidation confound:**
The reaction Cu + 2FeO + O2 -> CuFe2O4 does TWO things simultaneously:
1. Captures Cu (Cu0 -> Cu2+) — the part we care about
2. Oxidizes Fe (2 x Fe2+ -> Fe3+) — a side reaction irrelevant to Cu removal

The Fe2+ -> Fe3+ oxidation with O2 is itself strongly exothermic. Literature analysis
estimates that **~70-80% of the -112 kJ driving force comes from iron oxidation**, not
copper capture. The actual Cu-capture energy is approximately **-20 to -40 kJ/mol** —
comparable to CuAl2O4's -32 kJ, where Al3+ doesn't change oxidation state.

**Steelmaking conditions kill this reaction:**
- CuFe2O4 formation REQUIRES oxidizing conditions (high pO2)
- Steelmaking is strongly REDUCING (dissolved C, low pO2)
- Under reducing conditions, Fe3+ -> Fe2+ is favored, which DECOMPOSES CuFe2O4
- The equilibrium shifts: CuFe2O4 -> Cu + 2FeO + 0.5 O2 under reducing atmosphere
- CuFe2O4 is only stable at pO2 > ~10^-6 atm at 1200C (literature)

**Extrapolation concern:**
TCOX14 oxide data is calibrated primarily from room temperature to ~1200-1300C
experimental measurements [1, 11]. Most experimental thermochemistry for oxide
systems (drop calorimetry, EMF, gas equilibration) was conducted below ~1400C due
to container reactivity and sensor limitations [11, 14]. The CALPHAD models (Redlich-
Kister polynomials, compound energy formalism [4, 5]) fitted to this data can be
evaluated at any temperature, but extrapolation beyond the fitting range can produce
unphysical results [6]. For CuFe2O4 specifically, the foundational experimental data
was collected at ~1000C [10] and the most comprehensive Cu-Fe-O assessment covers
923-1273 K [9]. At 1527C (1800K), we are extrapolating ~500K beyond the calibration
range. The -112 kJ value at 1800K should be treated with caution. Formal uncertainty
quantification methods for CALPHAD predictions do not yet exist [8].

**Bottom line for our project:**
- CuFe2O4 is NOT a practical candidate for Cu removal from steel
- The -112 kJ is thermodynamically correct but physically irrelevant
- FeO is already present in steelmaking slag; if CuFe2O4 could form, it already would
- CuAl2O4's -32 kJ (where Al stays at +3) is a more honest measure of Cu capture energy
- **CuMn2O4 (-64 kJ) is likely the best "clean" candidate** — Mn goes from +2 to mixed
  +2/+3 in the spinel, which is a smaller redox contribution than Fe

**Validation needed:** Calculate dG for Cu + Fe2O3 -> CuFe2O4 (no O2 needed, Fe already
at +3). This isolates the Cu-capture contribution from the Fe-oxidation contribution.
Comparing the two reactions quantifies exactly how much of the -112 kJ is from iron
oxidation. (See Section 7 for TC-Python validation plan.)

### 5.3 CeO2 Not in TCOX14

The Ce element is not available in the TCOX14 database. CuCeO3 could not be modeled.
Binary CeO2 data was obtained from SSUB3 database in Phase 1, but SSUB3 does not
support ternary equilibrium calculations. If CeO2 ternary data is needed, alternative
databases or literature values would be required.

### 5.4 V2O5 Reference Convergence

The V2O5 binary oxide reference calculation failed at T = 1050 K and T = 1300 K
(TC convergence error: TOO MANY ITERATIONS). This creates 2 missing data points
each for CuV2O6 and Cu3V2O8. The missing points could be linearly interpolated
from neighboring temperatures if needed.

---

## 6. Top Candidates for Experimental Validation

### Tier 1: Strong Thermodynamic Evidence

| Oxide | Best Product | dG (kJ) | Spinel Stable To | Practical Notes |
|-------|-------------|---------|------------------|-----------------|
| MnO   | CuMn2O4    | -64.4   | 1427C            | Best "clean" candidate. Cheap, non-toxic, common in steelmaking. Mn2+->Mn3+ contributes some energy but less than Fe case. |
| V2O5  | Cu3V2O8    | -109.2  | (liquid)         | Literature backing (Bureau of Mines: 40-60% removal). HIGH toxicity (Carc. 1B). -36 kJ per Cu atom. |
| SiO2  | Cu2SiO4    | -52.2   | (liquid)         | No named phase but strong dG. SiO2 already in slag. -26 kJ per Cu atom. |

### Tier 2: Good Candidates with Caveats

| Oxide | Best Product | dG (kJ) | Notes |
|-------|-------------|---------|-------|
| B2O3  | CuB2O4     | -47.7   | Named phase found (to 1027C). Borate slag dissolution mechanism. Moderate toxicity. |
| Al2O3 | CuAl2O4    | -32.3   | Known to work (Year 2 data). Use as positive control. Spinel melts at 1277C. |
| FeO   | CuFe2O4    | -111.9  | **DEMOTED.** ~70-80% of dG is from Fe2+->Fe3+ oxidation, not Cu capture. Requires oxidizing conditions absent in steelmaking. Actual Cu-capture energy ~20-40 kJ. Already present in slag. |

### Recommendation for Zhang Meeting

Test 3 oxides experimentally:
1. **Al2O3** — positive control (known to capture some Cu via CuAl2O4 spinel)
2. **MnO** — strongest "clean" candidate (no Fe oxidation confound, cheap, non-toxic)
3. **V2O5** — strongest literature backing (Bureau of Mines 40-60% removal), if toxicity manageable

Optional 4th: **SiO2** — already in steelmaking slag, strong dG, cheap, safe

---

## 7. Additional TC-Python Validation Plan

### 7.1 Isothermal Phase Diagrams (Cu-M-O at 1527C)

For the top 3-4 candidates, calculate ternary phase diagrams at steelmaking temperature.
These would show:
- Equilibrium phase regions across the full composition space
- Whether a CuMOy phase field exists at the target stoichiometry
- The extent of Cu solubility in the oxide phases
- Phase boundaries relevant to experimental conditions

### 7.2 Cu Activity Calculations

Calculate the activity of Cu (a_Cu) as a function of oxide addition. If a_Cu drops
significantly in the ternary system compared to pure Cu, that directly measures
the "capture" effect. This is the experimental observable — lower a_Cu means less
Cu available to partition into the steel.

### 7.3 Alternative Reaction for CuFe2O4

Calculate dG for: Cu + Fe2O3 -> CuFe2O4 (no O2 needed, Fe already at +3)
This isolates the Cu-capture energy from the Fe-oxidation energy. Comparing
this to the FeO-based reaction tells us how much of the -112 kJ is from
iron oxidation vs. genuine copper capture.

### 7.4 Property Diagrams (dG vs T)

Generate continuous dG vs. temperature curves for the top 5-6 products.
These would show:
- Exact temperatures of phase transitions (kinks in the curve)
- Smooth data for PowerPoint figures
- Crossover points where one product becomes more favorable than another

### 7.5 Slag Composition Effects

For the most promising oxides (FeO, MnO, Al2O3), calculate dG as a function
of slag composition (e.g., vary FeO/SiO2 ratio in a ternary slag). This is
directly relevant to industrial conditions where the oxide is part of a
multi-component slag, not a pure phase.

---

## 8. Files and Data

### Scripts
- `simulations/tcpython/extract_ternary_reactions.py` — TC-Python extraction (run on VM)
- `screening/compute_ternary_dG.py` — local post-processing and ranking
- `screening/build_combined_screening.py` — unified 7-tab Excel workbook builder

### Data
- `data/tcpython/raw/ternary_reaction_energies.csv` — raw TC-Python output (414 rows)
- `screening/ternary_screening_results.csv` — processed results with verdicts
- `screening/Cu_Removal_Screening.xlsx` — combined workbook (7 tabs)

### VM Terminal Logs
- `F March 13 Complexes Run TC Python.rtf` — binary oxide re-extraction log
- `F Mar 13 2nd Run.rtf` — ternary extraction log (the successful run)

---

## 9. Verification Summary

| Check | Status | Notes |
|-------|--------|-------|
| Atom balance (all 18 reactions) | PASS | LHS atoms = RHS atoms for every reaction |
| Temperature coverage | 15 products: 23/23; 2 products (V2O5): 21/23; CeO3: 0/23 | V2O5 ref failed at 1050K, 1300K |
| dG trend (less negative at higher T) | PASS | Small reversals at phase transitions are physical |
| GM values in expected range | PASS | All between -120k and -350k J/mol-atoms |
| G_Cu and G_O2 reference consistency | PASS | Identical values at same T across all products |
| No NaN/inf/empty dG values | PASS | (except CeO3 and 4 V2O5 points noted above) |
| Mole fractions sum to 1.0 | PASS | Verified in script and independently |

---

## 10. References

### TCOX14 Database and Assessment Papers
[1] Thermo-Calc Software, "TCS Metal Oxide Solutions Database (TCOX14) Technical Information."
    https://thermocalc.com/products/databases/metal-oxide-solutions/

[2] D. Dilner, L. Kjellqvist, H. Mao, et al., "Improving Steel and Steelmaking — an Ionic
    Liquid Database for Alloy Process Design," Integrating Materials and Manufacturing
    Innovation, vol. 7, pp. 195-201, 2018. DOI: 10.1007/s40192-018-0121-z

[3] L. Kjellqvist, M. Selleby, and B. Sundman, "Thermodynamic modelling of the Cr-Fe-Ni-O
    system," CALPHAD, vol. 32, no. 3, pp. 577-592, 2008. DOI: 10.1016/j.calphad.2008.04.001

### CALPHAD Method
[4] H. L. Lukas, S. G. Fries, and B. Sundman, Computational Thermodynamics: The Calphad
    Method, Cambridge University Press, 2007. ISBN: 9780521868112

[5] M. Hillert, "The compound energy formalism," Journal of Alloys and Compounds, vol. 320,
    no. 2, pp. 161-176, 2001. DOI: 10.1016/S0925-8388(00)01481-X

### Extrapolation Reliability
[6] B. Sundman, U. R. Kattner, M. Hillert, M. Selleby, et al., "A method for handling the
    extrapolation of solid crystalline phases to temperatures far above their melting point,"
    CALPHAD, vol. 68, 101737, 2020. DOI: 10.1016/j.calphad.2020.101737
    — Demonstrates unphysical results from polynomial extrapolation beyond fitting range

[7] S. Gorsse and O. N. Senkov, "About the Reliability of CALPHAD Predictions in
    Multicomponent Systems," Entropy, vol. 20, no. 12, 899, 2018. DOI: 10.3390/e20120899
    — Shows comprehensive databases assess only ~5% of possible ternary systems

[8] U. R. Kattner, "The CALPHAD Method and Its Role in Material and Process Development,"
    Tecnologia em Metalurgia, Materiais e Mineracao, vol. 13, no. 1, pp. 3-15, 2016.
    DOI: 10.4322/2176-1523.1059
    — States "currently no such methods exist" for formal CALPHAD uncertainty quantification

### CuFe2O4 Experimental Data
[9] D. Shishin, T. Hidayat, E. Jak, and S. A. Decterov, "Critical assessment and thermodynamic
    modeling of the Cu-Fe-O system," CALPHAD, vol. 41, pp. 160-179, 2013.
    DOI: 10.1016/j.calphad.2013.04.001
    — Most comprehensive Cu-Fe-O CALPHAD assessment; experimental data mainly 923-1273 K

[10] K. T. Jacob, K. Fitzner, and C. B. Alcock, "Activities in the spinel solid solution, phase
     equilibria and thermodynamic properties of ternary phases in the system Cu-Fe-O,"
     Metallurgical Transactions B, vol. 8, pp. 451-460, 1977. DOI: 10.1007/BF02696932
     — Foundational EMF measurements for CuFe2O4, data at ~1000°C

### High-Temperature Oxide Calorimetry
[11] A. Navrotsky, "Progress and New Directions in Calorimetry: A 2014 Perspective," Journal of
     the American Ceramic Society, vol. 97, no. 11, pp. 3349-3359, 2014.
     DOI: 10.1111/jace.13278
     — Documents that conventional oxide thermochemistry is limited to ~1200-1400°C

[12] O. Fabrichnaya, S. K. Saxena, P. Richet, and E. F. Westrum, Thermodynamic Data, Models,
     and Phase Diagrams in Multicomponent Oxide Systems, Springer, 2004.
     — Tables cover 298-1800 K, reflecting practical upper limit of available data

---

*Last updated: March 13, 2026 (late evening session)*
