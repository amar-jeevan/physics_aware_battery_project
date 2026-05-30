# Physics-Aware LFP Battery Energy Storage Model

A physics-based Python simulation of a LiFePO₄ (LFP) battery energy storage system under renewable generation and load demand. The model couples electrical behaviour (SOC evolution) with thermal dynamics through temperature-dependent internal resistance, parameterised from published LFP cell data.

---

## What this project does

Most battery storage simulations assume constant efficiency and ignore thermal behaviour. This project adds a physics-aware layer:

- **SOC evolution** with temperature-dependent coulombic efficiency η(T)
- **Temperature-dependent internal resistance** R(T) — polynomial fitted from published A123 LFP cell data
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

Temperature-dependent internal resistance — A123 ANR26650M1-B LFP, HPPC-identified at ~50% SOC:

```
R(T) = 0.02832 − 0.001604·T + 0.0000285·T²   [Ω]
     ≈ 28.3   − 1.60·T     + 0.028·T²         [mΩ]

Valid: −10 °C to +40 °C,  ~50% SOC,  fresh cell
Fit:  R² = 0.961,  RMSE = 2.97 mΩ
```

SOC update with temperature-dependent coulombic efficiency:

```
SOC(t+1) = SOC(t) + η(T)·P_charge·Δt / E_capacity        (charging)
SOC(t+1) = SOC(t) − P_discharge·Δt / (η(T)·E_capacity)   (discharging)
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
│   ├── lfp_resistance_temperature.csv     ← R(T) data with full source provenance
│   ├── lfp_ocv_soc_temperature.csv        ← OCV(SOC, T) table — Stage 2C ready
│   ├── raw/                               ← place downloaded raw datasets here
│   └── processed/                         ← outputs from data loading scripts
│
├── src/
│   ├── battery.py                         ← BatteryParams + PhysicsAwareBattery
│   ├── resistance_fit.py                  ← R(T) polynomial fit, metrics, plot
│   ├── data_loader.py                     ← loaders for Catenaro / Chin / CALCE
│   ├── profiles.py                        ← synthetic solar + load profiles
│   ├── simulation.py                      ← dispatch loop
│   ├── metrics.py                         ← energy served, curtailment, efficiency
│   └── plots.py                           ← result visualisations
│
├── examples/
│   └── run_stage1.py                      ← end-to-end simulation entry point
│
├── tests/
│   └── test_basic.py                      ← unit tests
│
└── results/                               ← generated plots and CSV (gitignored)
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

To run only the R(T) fit and regenerate the plot:

```bash
python src/resistance_fit.py
```

---

## Cell and thermal parameters

All parameters sourced from published literature for the **A123 Systems ANR26650M1-B LFP 26650** cell.

| Parameter | Value | Source |
|---|---|---|
| Internal resistance R₀ at 25°C | 10.0 mΩ | Lin et al. 2013 [1] |
| R(T) polynomial valid range | −10 to +40 °C | Lin 2013 / Forgez 2010 [2] |
| Specific heat capacity Cₚ | **810.53 J/kg/K** | Gao et al. 2017, Table 1 [3] |
| Cell mass | 76 g | Gao et al. 2017, Table 1 [3] |
| C per cell (lumped) | 61.6 J/K | m × Cₚ |
| Convective h (still air) | 0.0745 W/K per cell | hconv × Sarea, Gao 2017 [3] |
| Thermal time constant τ | ~14 min per cell | C / h, still air |
| Cooling coeff (forced air, pack) | 80 W/K | Scaled from Forgez 2010 [2] |

> **Note on Cₚ:** The paper-measured value of 810.53 J/kg/K (Gao 2017) is used. Earlier literature estimates of ~1100 J/kg/K are within the spread reported across LFP studies but less specific to this cell.

---

## R(T) data provenance

The resistance polynomial is fitted from HPPC-identified R₀ values for the A123 LFP cell. Two resistance definitions exist in the literature and the difference matters:

| Source | Method | R₀ at 25°C, 50% SOC | Definition |
|---|---|---|---|
| Lin et al. 2013 [1] | HPPC 10-s pulse, high resolution | ~10 mΩ | Pure ohmic drop (sub-ms) |
| Gao et al. 2017 [3] | 1-sample/s instantaneous rise | ~65–80 mΩ | Ohmic + fast RC within 1 s |
| CALCE A123 DST (this project) | Dynamic profile ΔV/ΔI | ~165 mΩ | Effective dynamic resistance |

**This model uses the Lin 2013 values** because R(T) enters the heat generation term Q_gen = I²·R(T), for which the pure ohmic resistance is physically correct. The Gao 2017 and CALCE values represent different measurement concepts and would overestimate ohmic heating.

The CALCE result (165 mΩ at 25°C) is retained in `data/processed/` as a validated demonstration that dynamic profiles capture effective resistance rather than ohmic R₀ — a finding documented in the project methodology.

---

## Stage roadmap

### ✅ Stage 1 — Core physics model
- Synthetic solar and load profiles
- SOC model with temperature-dependent efficiency
- Lumped thermal model with semi-implicit Euler
- Fixed-point thermal-electrical iteration (Picard)
- Performance metrics and plots

### ✅ Stage 2A — LFP resistance model (literature values)
- R(T) polynomial from Lin 2013 / Forgez 2010 HPPC data
- `data/lfp_resistance_temperature.csv` with source provenance
- `src/resistance_fit.py` — fitting, RMSE/MAE/R², validation plot
- Thermal parameters corrected (cooling_coeff 12 → 80 W/K)

### ✅ Stage 2B — Paper-sourced thermal parameters + data investigation
- Thermal parameters updated from Gao et al. 2017 Table 1: Cₚ = 810.53 J/kg/K
- Cell-level thermal time constant calculated and documented: τ ≈ 14 min
- CALCE A123 DST investigation: confirmed dynamic profiles yield R_eff ≠ R₀
  - R_eff ≈ 165 mΩ at 25°C (factor of ~6 above ohmic R₀) — documented finding
- `data/lfp_ocv_soc_temperature.csv` added — OCV(SOC, T) from Gao 2017 Fig. 10/11
- R(T) definition difference between measurement methods documented
- **Stage 1 → 2B comparison:** max temp 65.9°C → 26.0°C, iterations 30 → 4

### 🔲 Stage 2C — Validation against experimental discharge data
- Load Catenaro & Onori 2021 discharge data (Mendeley, CC BY 4.0)
  - `https://data.mendeley.com/datasets/kxsbr4x3j2/2`
- Simulate discharge at 5°C, 25°C, 35°C
- Overlay simulated T(t) against measured cell surface temperature
- Report RMSE and MAE — validation table

### 🔲 Stage 3 — Equivalent circuit model (ECM)
- OCV(SOC, T) lookup table using `lfp_ocv_soc_temperature.csv`
- 1-RC transient voltage model: U_L = U_OC − I·R₀ − U₁
- Simulated vs measured terminal voltage curves
- ECM architecture follows Gao et al. 2017 [3]

### 🔲 Stage 4 — Full multi-temperature validation
- Run Stage 3 model at 5/15/25/45°C
- Validation plots at each temperature (Figures 17–20 style from Gao 2017)
- RMSE table across temperatures

---

## Key result: Stage 1 → Stage 2B comparison

| Metric | Stage 1 | Stage 2B | Change |
|---|---|---|---|
| R(25°C) | 85 mΩ (placeholder) | 10.0 mΩ (Lin 2013 HPPC) | −88% |
| Cₚ | 1100 J/kg/K (assumed) | 810.53 J/kg/K (Gao 2017, measured) | −26% |
| Max temperature | 65.9°C | 26.0°C | −40°C |
| Hours above 45°C | 12/24 | 0/24 | Eliminated |
| Fixed-point iterations (max) | 30 | 4 | 7.5× faster |
| Average efficiency | 95.68% | 95.99% | +0.31 pp |

---

## Why this project matters

This project demonstrates physics-based system modelling, numerical methods (fixed-point iteration, semi-implicit Euler), thermal-electrical coupling, parameter identification from experimental literature, and engineering validation methodology. It is intended as a portfolio project for energy systems, storage modelling, simulation engineering, and research-oriented roles.

---

## References

1. **Lin, X., Perez, H.E., Siegel, J.B., Stefanopoulou, A.G. et al. (2013).** *IEEE Trans. Control Systems Technology*, 22(7). DOI: [10.1109/TCST.2013.2278763](https://doi.org/10.1109/TCST.2013.2278763) — HPPC R₀(T) identification, A123 ANR26650M1A LFP.

2. **Forgez, C., Do, D.V., Friedrich, G., Morcrette, M., Delacourt, C. (2010).** *J. Power Sources*, 195(9), 2961–2968. DOI: [10.1016/j.jpowsour.2009.10.105](https://doi.org/10.1016/j.jpowsour.2009.10.105) — Lumped thermal model, Cₚ, Rin, Rout for A123 26650 LFP.

3. **Gao, Z., Chin, C.S., Woo, W.L., Jia, J. (2017).** *Energies*, 10(1):85. DOI: [10.3390/en10010085](https://doi.org/10.3390/en10010085) — ECM + thermal model, A123 ANR26650M1-B; Cₚ = 810.53 J/kg/K, hconv, Sarea (Table 1); OCV(SOC, T) (Figs 10–11); R₀(SOC, T) (Fig. 13).

4. **Preger, Y. et al. (2020).** *J. Electrochem. Soc.*, 167, 120532. DOI: [10.1149/1945-7111/abae37](https://doi.org/10.1149/1945-7111/abae37) — Sandia/SNL LFP aging dataset, consistent R(T) trend.

5. **Schimpe, M. et al. (2018).** *Applied Energy*, 210, 211–229. DOI: [10.1016/j.apenergy.2017.10.129](https://doi.org/10.1016/j.apenergy.2017.10.129) — BESS electro-thermal dispatch reference.

6. **Catenaro, E., Onori, S. (2021).** *Data in Brief*, 35, 106894. DOI: [10.1016/j.dib.2021.106894](https://doi.org/10.1016/j.dib.2021.106894) — A123 LFP discharge data at 5/25/35°C (Stage 2C validation source).