import numpy as np


def synthetic_solar_profile(hours: int = 24, peak_kw: float = 120.0) -> np.ndarray:
    """
    Simple daily solar generation profile.

    Zero at night, sinusoidal during daytime.
    """
    t = np.arange(hours)
    solar = np.zeros(hours)

    daylight_start = 6
    daylight_end = 18
    daylight = (t >= daylight_start) & (t <= daylight_end)

    solar[daylight] = peak_kw * np.sin(
        np.pi * (t[daylight] - daylight_start) / (daylight_end - daylight_start)
    )

    return solar


def synthetic_load_profile(hours: int = 24, base_kw: float = 60.0) -> np.ndarray:
    """
    Simple residential/industrial mixed load profile.
    """
    t = np.arange(hours)
    morning_peak = 20.0 * np.exp(-0.5 * ((t - 8) / 2.0) ** 2)
    evening_peak = 35.0 * np.exp(-0.5 * ((t - 19) / 3.0) ** 2)
    daily_variation = 8.0 * np.sin(2 * np.pi * (t - 5) / 24)

    return base_kw + morning_peak + evening_peak + daily_variation
