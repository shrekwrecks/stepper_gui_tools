import pytest
from motion_planner import ramp_velocity


def test_ramp_start():
    """At t=0, velocity should equal the start velocity."""
    assert ramp_velocity(0, start_vel=5, target_vel=30, max_accel=10) == 5


def test_ramp_slope():
    """During the ramp, velocity should increase linearly with slope = max_accel."""
    v1 = ramp_velocity(0.5, start_vel=0, target_vel=30, max_accel=10)
    v2 = ramp_velocity(1.0, start_vel=0, target_vel=30, max_accel=10)
    # Expected slope ~ max_accel (10 units per sec)
    slope = v2 - v1
    assert pytest.approx(slope, rel=1e-2) == 10 * 0.5


def test_ramp_end():
    """At t = t_ramp, velocity should exactly equal target_vel."""
    start_vel = 0
    target_vel = 30
    max_accel = 10
    t_ramp = (target_vel - start_vel) / max_accel
    v = ramp_velocity(t_ramp, start_vel, target_vel, max_accel)
    assert pytest.approx(v, rel=1e-6) == target_vel


def test_hold_after_ramp():
    """After t_ramp, velocity should stay constant at target_vel."""
    start_vel = 0
    target_vel = 30
    max_accel = 10
    t_ramp = (target_vel - start_vel) / max_accel
    v_after = ramp_velocity(t_ramp + 5, start_vel, target_vel, max_accel)
    assert v_after == target_vel


def test_no_ramp_needed():
    """If start_vel == target_vel, velocity should remain constant."""
    v = ramp_velocity(10, start_vel=20, target_vel=20, max_accel=5)
    assert v == 20


def test_negative_ramp():
    """If target_vel < start_vel, the ramp should decelerate with slope = -max_accel."""
    start_vel = 30
    target_vel = 0
    max_accel = 10
    t_ramp = (target_vel - start_vel) / max_accel  # should be negative
    # Ramp is in reverse, so check slope
    v1 = ramp_velocity(0.5, start_vel=start_vel, target_vel=target_vel, max_accel=max_accel)
    v2 = ramp_velocity(1.0, start_vel=start_vel, target_vel=target_vel, max_accel=max_accel)
    assert v2 < v1


if __name__ == "__main__":
    pytest.main([__file__])
