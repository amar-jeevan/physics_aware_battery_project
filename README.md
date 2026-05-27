# Physics-Aware LFP Battery Energy Storage Model

A physics-based Python simulation of a LiFePO₄ (LFP) battery energy storage system under renewable generation and load demand. The model couples electrical behaviour (SOC evolution) with thermal dynamics through temperature-dependent internal resistance, validated against published LFP cell data.

---

## What this project does

Most battery storage simulations assume constant efficiency and ignore thermal behaviour. This project adds a physics-aware layer:

- **State of charge (SOC)** evolution with temperature-dependent charging/discharging efficiency η(T)
- **Temperature-dependent internal resistance** R(T) — polynomial fit from published A123 LFP cell data
- **Joule heating** Q_gen = I²·R(T)
- **Lumped thermal model** with semi-implicit Euler integration for numerical stability
- **Fixed-point (Picard) iteration** at each timestep to converge the coupled R(T)–T system
- **Renewable dispatch loop** — solar generation profile, load demand, battery control logic, grid exchange metrics

---

## Technical model

Power balance at each timestep:

```
P_net = P_generation − P_load
```

Battery temperature evolves via a lumped thermal ODE (semi-implicit Euler):

```
C · dT/dt = Q_gen − Q_loss
         = I²·R(T) − h·(T − T_ambient)
```

Temperature-dependent internal resistance (LFP, A123 ANR26650M1A):

```
R(T) = 0.02832 − 0.001604·T + 0.0000285·T²   [Ω]
     ≈ 28.3 − 1.60·T + 0.028·T²              [mΩ]

Valid: −10 °C to +40 °C, ~50% SOC, fresh cell
Fit:  R² = 0.961,  RMSE = 2.97 mΩ
```

Sources: Lin et al. (2013) IEEE TCST [DOI: 10.1109/TCST.2013.2278763],
Forgez et al. (2010) J. Power Sources [DOI: 10.1016/j.jpowsour.2009.10.105],
consistent with Sandia/Preger (2020) [DOI: 10.1149/1945-7111/abae37].

SOC update with temperature-dependent coulombic efficiency:

```
SOC(t+1) = SOC(t) + η(T)·P_charge·Δt / E_capacity    (charging)
SOC(t+1) = SOC(t) + P_discharge·Δt / (η(T)·E_capacity) (discharging)
```

---

## Repository structure

```
physics_aware_battery_project/
│
├── README.md
├── requirements.txt
│
├── data/
│   └── lfp_resistance_temperature.csv   ← LFP R(T) data with source provenance
│
├── src/
│   ├── battery.py           ← BatteryParams dataclass + PhysicsAwareBattery class
│   ├── resistance_fit.py    ← R(T) polynomial fit, metrics, validation plot
│   ├── profiles.py          ← Synthetic solar + load profiles
│   ├── simulation.py        ← Dispatch loop
│   ├── metrics.py           ← Energy served, curtailment, efficiency metrics
│   └── plots.py             ← Result visualisations
│
├── examples/
│   └── run_stage1.py        ← End-to-end simulation entry point
│
├── tests/
│   └── test_basic.py        ← Unit tests
│
└── results/                 ← Generated plots and CSV (gitignored)
```

---

## How to run

```bash
pip install -r requirements.txt
python examples/run_stage1.py
```

This will:
1. Fit the LFP R(T) polynomial and print coefficients + fit metrics
2. Save `results/lfp_resistance_fit.png` — measured data vs polynomial fit
3. Run the 24-hour dispatch simulation
4. Print performance metrics
5. Save simulation plots to `results/`

To run only the R(T) fit:

```bash
python src/resistance_fit.py
```

---

## Thermal parameters (Stage 2A)

| Parameter | Value | Source |
|---|---|---|
| Specific heat Cp | 1100 J/kg/K | Lin et al. 2022 (DOI: 10.1002/batt.202100401) |
| Lumped thermal capacity C | 75,000 J/K | ~70 cells × 975 g × 1100 J/kg/K (pack estimate) |
| Cooling coefficient h | 80 W/K | Forced-air BESS rack; Forgez et al. 2010 baseline |
| Valid temperature range | −10 °C to +40 °C | Li-ion safe operating range |

---

## Stage roadmap

### ✅ Stage 1 — Core physics model
- Synthetic solar and load profiles
- SOC model with temperature-dependent efficiency
- Lumped thermal model with semi-implicit Euler
- Fixed-point thermal-electrical iteration
- Basic performance metrics and plots

### ✅ Stage 2A — LFP resistance model
- R(T) polynomial fitted from published A123 LFP data (Lin 2013, Forgez 2010)
- `data/lfp_resistance_temperature.csv` with full source provenance
- `src/resistance_fit.py` — fitting, metrics (RMSE, MAE, R²), validation plot
- Corrected thermal parameters (cooling_coeff 12 → 80 W/K)
- Results: max temp 65.9 °C → 26.0 °C; fixed-point iterations 15 → 4

### 🔲 Stage 2B — Raw data fitting
- Download CALCE A123 DST files (0–50 °C) from https://calce.umd.edu/battery-data
- Download Sandia/SNL LFP CSV from https://www.batteryarchive.org
- Re-fit `polyfit` against measured HPPC pulse IR; replace `lfp_resistance_temperature.csv`
- Extend valid range to 0–50 °C with higher-confidence fit

### 🔲 Stage 2C — Validation
- Load NASA PCoE B0005 discharge data (parser pipeline demo)
- Overlay simulated vs measured temperature and voltage curves
- Report RMSE and MAE in a validation table

### 🔲 Stage 3 — Extensions
- SOC-dependent OCV model
- Equivalent circuit model (Thevenin RC)
- Multi-day / weekly simulation
- Battery sizing optimisation

---

## Key result: Stage 1 → Stage 2A comparison

| Metric | Stage 1 (placeholder) | Stage 2A (LFP-fitted) | Change |
|---|---|---|---|
| R(25 °C) | 85 mΩ (generic) | 28.3 mΩ (LFP A123) | −67% |
| Max temperature | 65.9 °C | 26.0 °C | −40 °C |
| Hours above 45 °C | 12 / 24 | 0 / 24 | Eliminated |
| Fixed-point iterations (max) | 15 | 4 | 4× faster |
| Average efficiency | 95.68% | 95.99% | +0.31 pp |
| Local energy served | 48.22% | 48.25% | +0.03 pp |

---

## Why this project matters

This project demonstrates physics-based system modelling, numerical methods (fixed-point iteration, semi-implicit integration), thermal-electrical coupling, and engineering validation against published experimental data. It is intended as a portfolio project for energy systems, storage modelling, simulation engineering, and research-oriented applications.

---

## References

1. Lin, X., Perez, H.E., Siegel, J.B., Stefanopoulou, A.G. et al. (2013). *IEEE Trans. Control Systems Technology*, 22(7). DOI: [10.1109/TCST.2013.2278763](https://doi.org/10.1109/TCST.2013.2278763)
2. Forgez, C., Do, D.V., Friedrich, G., Morcrette, M., Delacourt, C. (2010). *J. Power Sources*, 195(9), 2961–2968. DOI: [10.1016/j.jpowsour.2009.10.105](https://doi.org/10.1016/j.jpowsour.2009.10.105)
3. Preger, Y., Barkholtz, H.M., Fresquez, A. et al. (2020). *J. Electrochem. Soc.*, 167, 120532. DOI: [10.1149/1945-7111/abae37](https://doi.org/10.1149/1945-7111/abae37)
4. Lin, J., Chu, V., Monroe, C., Howey, D.A. (2022). *Batteries & Supercaps*, 5(5), e202100401. DOI: [10.1002/batt.202100401](https://doi.org/10.1002/batt.202100401)
5. Schimpe, M. et al. (2018). *Applied Energy*, 210, 211–229. DOI: [10.1016/j.apenergy.2017.10.129](https://doi.org/10.1016/j.apenergy.2017.10.129)