import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from battery import BatteryParams, PhysicsAwareBattery


def test_resistance_positive():
    battery = PhysicsAwareBattery(BatteryParams())
    assert battery.resistance_ohm(25.0) > 0


def test_efficiency_range():
    battery = PhysicsAwareBattery(BatteryParams())
    eta = battery.efficiency(25.0)
    assert 0.0 < eta <= 1.0


def test_coupled_step_runs():
    battery = PhysicsAwareBattery(BatteryParams())
    state = battery.solve_coupled_step(10.0)
    assert "temperature_c" in state
    assert "soc" in state
    assert state["iterations"] > 0
