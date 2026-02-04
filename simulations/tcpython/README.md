# TC-Python Scripts

Scripts for extracting thermodynamic data from Thermo-Calc on OSU lab machines.

## Available Scripts

| Script | Purpose |
|--------|---------|
| `check_databases.py` | **Run first!** Lists available databases and phases |
| `extract_oxide_gibbs.py` | Extracts Gibbs energies for Ellingham diagram (Al2O3, MgO, etc.) |
| `cu_al_o_phase_stability.py` | Cu-Al-O ternary phase diagram calculations |

## Quick Start (Lab Machine)

### Step 1: Get the scripts onto the lab machine

**Option A: Download ZIP from GitHub**
1. Go to https://github.com/dimascad/honda-calphad
2. Click green "Code" button → "Download ZIP"
3. Extract to `C:\Users\YOUR_NAME\Documents\honda-calphad`

**Option B: Git clone (if git is installed)**
```cmd
cd C:\Users\YOUR_NAME\Documents
git clone https://github.com/dimascad/honda-calphad.git
```

### Step 2: Run a script

```cmd
cd C:\Users\YOUR_NAME\Documents\honda-calphad\simulations\tcpython
"C:\Program Files\Thermo-Calc\2025b\python\python.exe" check_databases.py
```

Or use the batch file:
```cmd
run_on_lab.bat check_databases.py
```

### Step 3: Get results back

Output goes to: `data\tcpython\raw\`

**Option A: Copy files manually**
- Copy the CSV files to OneDrive, USB, or email to yourself

**Option B: Git push (if available)**
```cmd
git add data/tcpython/
git commit -m "TC-Python: oxide Gibbs energies"
git push
```

## TC-Python Path

```
C:\Program Files\Thermo-Calc\2025b\python\python.exe
```

## Database Reference

| Database | Contents |
|----------|----------|
| SSUB6/SSUB5 | Pure substances - Gibbs energies |
| TCOX14 | Oxide systems (Cu-Al-O, etc.) |
| TCFE14 | Steel/iron systems |
| TCCU6 | Copper alloys |

Run `check_databases.py` first to see what's actually available!

## Output Format

Scripts output CSV files to `../../data/tcpython/raw/`:

```
T_K,T_C,dG_Cu2O_per_O2,dG_CuO_per_O2,dG_Al2O3_per_O2,...
500,226.85,-264000,-220000,-1010000,...
```

These can be loaded directly into the visualization notebooks.
