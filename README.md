# Physics-Aware Battery Energy Storage Model

A compact Python project for analysing battery energy storage behaviour under renewable generation and load demand, with a coupled thermal-electrical battery model.

## Project idea

Most simple battery storage simulations assume constant efficiency and ignore thermal behaviour. This project adds a physics-aware layer:

- State of charge (SOC) evolution
- Temperature-dependent internal resistance `R(T)`
- Heat generation using `I²R`
- Lumped thermal cooling model
- Fixed-point iteration at each time step to converge battery temperature and current

The long-term goal is to extend this into a validation-ready modelling project using published Li-ion discharge data.

## Technical model

At each time step, the net power is:

```text
P_net = P_generation - P_load
```

If generation exceeds load, the battery charges. If load exceeds generation, the battery discharges.

The battery temperature evolves according to:

```text
C_th dT/dt = Q_gen - Q_loss
```

with:

```text
Q_gen = I² R(T)
Q_loss = h (T - T_ambient)
```

The internal resistance is currently represented by a polynomial:

```text
R(T) = a0 + a1 T + a2 T²
```

In later stages, this will be replaced by a polynomial fit from published Li-ion cell data.

## Repository structure

```text
physics-aware-battery-storage/
│
├── README.md
├── requirements.txt
├── src/
│   ├── battery.py
│   ├── profiles.py
│   ├── simulation.py
│   ├── metrics.py
│   └── plots.py
│
├── examples/
│   └── run_stage1.py
│
├── tests/
│   └── test_basic.py
│
└── results/
```

## How to run

```bash
pip install -r requirements.txt
python examples/run_stage1.py
```

The script will generate plots in the `results/` folder.

## Current Stage

Stage 1 includes:

- Synthetic solar profile
- Synthetic load profile
- Battery SOC model
- Lumped thermal model
- Fixed-point thermal-electrical iteration
- Basic performance metrics
- Plots for generation/load, SOC, temperature, and grid exchange

## Planned future additions

1. Replace synthetic `R(T)` with polynomial fit from published Li-ion data.
2. Add validation against published experimental discharge data.
3. Add SOC-dependent open-circuit voltage model.
4. Add equivalent circuit model (ECM).
5. Add battery sizing scenarios for energy-sector analysis.
6. Add a Streamlit dashboard for interactive scenario exploration.

## Why this project matters

This project demonstrates physics-based system modelling, numerical iteration, thermal-electrical coupling, and engineering analysis. It is intended as a portfolio project for energy systems, storage modelling, simulation engineering, and research-oriented applications.
