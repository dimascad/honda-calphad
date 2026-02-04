# TC-Python Scripts

Scripts in this folder run on OSU lab machines with ThermoCalc 2025b.

## Setup (Lab Machine)

**Python path:**
```
C:\Program Files\Thermo-Calc\2025b\python\python.exe
```

**First time only:**
```cmd
cd C:\Users\dimascio.12\Documents
git clone https://github.com/dimascad/honda-calphad.git
```

## Workflow

### 1. Write scripts locally (your Mac)
Edit scripts in this folder using VS Code, then:
```bash
git add . && git commit -m "Update TC-Python script" && git push
```

### 2. Run on lab machine
```cmd
cd C:\Users\dimascio.12\Documents\honda-calphad
git pull
"C:\Program Files\Thermo-Calc\2025b\python\python.exe" simulations\tcpython\SCRIPT_NAME.py
```

### 3. Push results back
```cmd
git add data/tcpython/
git commit -m "TC-Python output: description"
git push
```

### 4. Pull results locally
```bash
git pull
# Data now in data/tcpython/ - analyze in Marimo
```

## TC-Python API Quick Reference

```python
from tc_python import *

with TCPython() as session:
    # List databases
    print(session.get_databases())

    # Set up system
    system = session.select_database_and_elements('TCOX14', ['Cu', 'Al', 'O'])

    # Equilibrium calculation
    calc = system.with_single_equilibrium_calculation()
    calc.set_condition('T', 1273)      # Temperature in Kelvin
    calc.set_condition('P', 101325)    # Pressure in Pa
    calc.set_condition('X(Al)', 0.4)   # Mole fraction
    calc.set_condition('X(O)', 0.5)

    result = calc.calculate()
    print(result.get_stable_phases())
```

## Available Databases (Relevant to Project)

| Database | Description |
|----------|-------------|
| TCOX14 | Oxide systems (Cu-Al-O phase diagrams) |
| TCCU6 | Copper alloys |
| TCFE14 | Iron/steel (Cu in Fe melt) |
| SSUB3 | Pure substances (Gibbs energies) |
| MOBCU5 | Copper mobility (diffusion) |

## Output Convention

Scripts should save data to `../../data/tcpython/raw/` as CSV or JSON.
Processing scripts on local machine move cleaned data to `processed/`.
