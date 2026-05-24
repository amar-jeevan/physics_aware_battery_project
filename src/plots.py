from pathlib import Path
import matplotlib.pyplot as plt


def plot_results(results, output_dir="results"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Plot 1: Generation and load
    plt.figure()
    plt.plot(results["step"], results["generation_kw"], label="Generation")
    plt.plot(results["step"], results["load_kw"], label="Load")
    plt.xlabel("Time step [h]")
    plt.ylabel("Power [kW]")
    plt.title("Generation vs Load")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "generation_vs_load.png", dpi=200)
    plt.close()

    # Plot 2: Battery SOC
    plt.figure()
    plt.plot(results["step"], results["soc"] * 100)
    plt.xlabel("Time step [h]")
    plt.ylabel("SOC [%]")
    plt.title("Battery State of Charge")
    plt.tight_layout()
    plt.savefig(output_dir / "battery_soc.png", dpi=200)
    plt.close()

    # Plot 3: Battery temperature
    plt.figure()
    plt.plot(results["step"], results["temperature_c"])
    plt.xlabel("Time step [h]")
    plt.ylabel("Temperature [°C]")
    plt.title("Battery Temperature")
    plt.tight_layout()
    plt.savefig(output_dir / "battery_temperature.png", dpi=200)
    plt.close()

    # Plot 4: Grid power exchange
    plt.figure()
    plt.plot(results["step"], results["grid_power_kw"])
    plt.axhline(0, linewidth=1)
    plt.xlabel("Time step [h]")
    plt.ylabel("Grid power [kW]")
    plt.title("Grid Power Exchange")
    plt.tight_layout()
    plt.savefig(output_dir / "grid_power_exchange.png", dpi=200)
    plt.close()
