from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Paths ──────────────────────────────────────────────────────────────────
_HERE       = Path(__file__).resolve().parent
_DATA_FILE  = _HERE.parent / "data" / "lfp_resistance_temperature.csv"
_RESULTS    = _HERE.parent / "results"

# ── Polynomial degree ──────────────────────────────────────────────────────
_POLY_DEGREE = 2


def load_lfp_data(csv_path: Path = _DATA_FILE) -> tuple[np.ndarray, np.ndarray]:
    """
    Load temperature (°C) and resistance (mΩ) arrays from the data CSV.
    Lines beginning with '#' are treated as comments and skipped.
    """
    df = pd.read_csv(csv_path, comment="#")
    return df["temperature_c"].to_numpy(), df["resistance_mohm"].to_numpy()


def fit_polynomial(
    temperature_c: np.ndarray,
    resistance_mohm: np.ndarray,
    degree: int = _POLY_DEGREE,
) -> np.ndarray:
    """
    Fit a polynomial of given degree to R(T) data.

    Returns coefficients [a_n, ..., a_1, a_0] in numpy.poly1d convention
    (highest degree first).  To evaluate: np.polyval(coeffs, T).
    """
    return np.polyfit(temperature_c, resistance_mohm, degree)


def polynomial_to_ohm(coeffs_mohm: np.ndarray) -> np.ndarray:
    """Convert polynomial coefficients from mΩ to Ω."""
    n = len(coeffs_mohm)
    scale = np.array([1e-3] * n)   # same scalar conversion for all terms
    return coeffs_mohm * scale


def load_lfp_coefficients_ohm(csv_path: Path = _DATA_FILE) -> tuple[float, float, float]:
    """
    Public API used by battery.py.

    Returns (a0, a1, a2) in ohm such that:
        R(T) = a0 + a1*T + a2*T**2   [Ω]

    Note: numpy.polyfit returns [a2, a1, a0] (highest degree first).
    This function reverses the order so the tuple follows the model
    convention used in battery.py (lowest degree first).
    """
    T, R = load_lfp_data(csv_path)
    coeffs_mohm = fit_polynomial(T, R)          # [a2, a1, a0] in mΩ
    coeffs_ohm  = polynomial_to_ohm(coeffs_mohm)
    a2, a1, a0  = coeffs_ohm                    # unpack highest-to-lowest
    return a0, a1, a2                            # return lowest-to-highest


def compute_fit_metrics(
    temperature_c: np.ndarray,
    resistance_mohm: np.ndarray,
    coeffs_mohm: np.ndarray,
) -> dict:
    """Return RMSE and MAE of the polynomial fit in mΩ."""
    fitted   = np.polyval(coeffs_mohm, temperature_c)
    residuals = resistance_mohm - fitted
    return {
        "rmse_mohm": float(np.sqrt(np.mean(residuals**2))),
        "mae_mohm":  float(np.mean(np.abs(residuals))),
        "max_err_mohm": float(np.max(np.abs(residuals))),
        "r_squared": float(
            1 - np.sum(residuals**2) / np.sum((resistance_mohm - resistance_mohm.mean())**2)
        ),
    }


def plot_resistance_fit(
    temperature_c: np.ndarray,
    resistance_mohm: np.ndarray,
    coeffs_mohm: np.ndarray,
    metrics: dict,
    output_dir: Path = _RESULTS,
) -> Path:
    """
    Save a publication-quality R(T) fit plot to output_dir.

    Returns the path of the saved PNG.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    T_smooth = np.linspace(temperature_c.min() - 2, temperature_c.max() + 2, 300)
    R_smooth = np.polyval(coeffs_mohm, T_smooth)

    # ── Style ──────────────────────────────────────────────────────────────
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.plot(
        T_smooth, R_smooth,
        color="#2563EB", linewidth=2.2, label="Polynomial fit (2nd order)",
        zorder=3,
    )
    ax.scatter(
        temperature_c, resistance_mohm,
        color="#DC2626", s=70, zorder=5,
        label="Published data (A123 LFP, Lin 2013 / Forgez 2010)",
        edgecolors="white", linewidths=0.8,
    )

    # Residual bars
    for T_i, R_i in zip(temperature_c, resistance_mohm):
        R_fit_i = np.polyval(coeffs_mohm, T_i)
        ax.plot(
            [T_i, T_i], [R_i, R_fit_i],
            color="#F59E0B", linewidth=1.4, zorder=4,
        )

    # Equation annotation
    a2, a1, a0 = coeffs_mohm
    eq_str = (
        f"R(T) = {a0:.2f} "
        f"{'−' if a1 < 0 else '+'} {abs(a1):.3f}·T "
        f"{'−' if a2 < 0 else '+'} {abs(a2):.4f}·T²   [mΩ]"
    )
    ax.text(
        0.97, 0.95, eq_str,
        transform=ax.transAxes, ha="right", va="top",
        fontsize=9.5, family="monospace",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#CBD5E1", alpha=0.9),
    )

    # Metrics annotation
    metrics_str = (
        f"RMSE = {metrics['rmse_mohm']:.2f} mΩ\n"
        f"MAE  = {metrics['mae_mohm']:.2f} mΩ\n"
        f"R²   = {metrics['r_squared']:.5f}"
    )
    ax.text(
        0.03, 0.95, metrics_str,
        transform=ax.transAxes, ha="left", va="top",
        fontsize=9, family="monospace",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#CBD5E1", alpha=0.9),
    )

    ax.set_xlabel("Temperature (°C)", fontsize=11)
    ax.set_ylabel("Internal Resistance (mΩ)", fontsize=11)
    ax.set_title(
        "LFP Internal Resistance vs Temperature\n"
        "A123 ANR26650M1A — Literature values + 2nd-order polynomial fit",
        fontsize=11, pad=10,
    )
    ax.legend(fontsize=9.5, loc="upper right", bbox_to_anchor=(0.97, 0.78))
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    plt.tight_layout()
    out_path = output_dir / "lfp_resistance_fit.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> None:
    T, R = load_lfp_data()
    coeffs_mohm = fit_polynomial(T, R)
    metrics = compute_fit_metrics(T, R, coeffs_mohm)

    a2, a1, a0 = coeffs_mohm
    a2_ohm, a1_ohm, a0_ohm = polynomial_to_ohm(coeffs_mohm)

    print("=" * 60)
    print("LFP R(T) polynomial fit — A123 ANR26650M1A")
    print("=" * 60)
    print(f"\nData points used: {len(T)}")
    print(f"Temperature range: {T.min()} °C to {T.max()} °C\n")
    print("Coefficients (mΩ, highest degree first):")
    print(f"  a2 = {a2:.6f}  mΩ/°C²")
    print(f"  a1 = {a1:.6f}  mΩ/°C")
    print(f"  a0 = {a0:.6f}  mΩ\n")
    print("Coefficients (Ω, for battery.py — lowest degree first):")
    print(f"  a0 = {a0_ohm:.8f}  Ω  (constant term)")
    print(f"  a1 = {a1_ohm:.8f}  Ω/°C")
    print(f"  a2 = {a2_ohm:.9f}  Ω/°C²\n")
    print(f"R(T) [mΩ] = {a0:.3f} + ({a1:.4f})*T + ({a2:.5f})*T²")
    print(f"R(T) [Ω]  = {a0_ohm:.6f} + ({a1_ohm:.7f})*T + ({a2_ohm:.8f})*T²\n")
    print("Fit metrics:")
    print(f"  RMSE    = {metrics['rmse_mohm']:.4f} mΩ")
    print(f"  MAE     = {metrics['mae_mohm']:.4f} mΩ")
    print(f"  Max err = {metrics['max_err_mohm']:.4f} mΩ")
    print(f"  R²      = {metrics['r_squared']:.6f}\n")

    out_path = plot_resistance_fit(T, R, coeffs_mohm, metrics)
    print(f"Plot saved to: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()