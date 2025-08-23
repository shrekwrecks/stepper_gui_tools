import matplotlib.pyplot as plt
import math
import numpy
import scipy


class Motor:
    def __init__(self, start_pos=0, start_vel=0):
        self.start_vel = start_vel
        self.pos = start_pos
        self.vel = start_vel
        self.accel = 0

    def update(self):

        self.vel = self.vel + self.accel
        self.pos = self.pos + self.vel


def ramp_velocity(t, start_vel=0, target_vel=30, max_accel=10):
    dv = target_vel - start_vel
    if dv == 0:
        return target_vel

    accel = max_accel if dv > 0 else -max_accel
    t_ramp = dv / accel

    if t < t_ramp:
        return start_vel + accel * t
    else:
        return target_vel


def s_curve_velocity(t, start_vel, start_accel, target_vel, max_accel, max_jerk):
    v_error = target_vel - start_vel
    direction = math.copysign(1, v_error)

    max_accel *= direction
    max_jerk *= direction

    v_min = (start_accel**2 + max_accel**2) / (2 * abs(max_jerk))
    if abs(v_error) < abs(v_min):
        peak_accel = math.sqrt(abs(v_error) * abs(max_jerk) + 0.5 * start_accel**2) * direction
        t_acc = (peak_accel - start_accel) / max_jerk
        t_cruise = 0.0
        t_dec = peak_accel / max_jerk
        t_total = t_acc + t_dec
        peak_accel_val = peak_accel
        # triangle
    else:
        t_acc = (max_accel - start_accel) / max_jerk
        t_dec = max_accel / max_jerk
        v_acc = (start_accel + max_accel) * t_acc * 0.5
        v_dec = max_accel * 0.5 * t_dec
        v_cruise = v_error - v_acc - v_dec
        t_cruise = v_cruise / max_accel
        t_total = t_acc + t_dec + t_cruise
        peak_accel_val = max_accel
        # trapezoid

        if t <= 0:
            return start_vel
        elif t <= t_acc:  # accelerating
            j = max_jerk
            a = start_accel + j * t
            v = start_vel + start_accel * t + 0.5 * j * t**2
        elif t <= t_acc + t_cruise:  # cruising
            j = 0.0
            a = peak_accel_val
            v = start_vel + (start_accel + peak_accel_val) / 2 * t_acc + peak_accel_val * (t - t_acc)
        elif t <= t_total:  # deceleratingp * (t - t
            td = t - (t_acc + t_cruise)
            j = max_jerk
            a = peak_accel_val + j * td
            v = v_acc + v_cruise + peak_accel_val * td - 0.5 * j * td**2
        else:  # finished
            return target_vel
        return v


if __name__ == "__main__":
    positions = []
    velocities = []
    accelerations = []

    sim_dt = 0.01
    sim_time = 10
    sim_iterations = int(sim_time / sim_dt)

    start_vel = 0
    start_accel = 0
    goal_vel = 30
    max_accel = 15
    max_jerk = 10
    motor = Motor(start_pos=0, start_vel=start_vel)

    for t in range(sim_iterations):
        motor.update()
        # motor.vel = ramp_velocity(t * sim_dt, start_vel, goal_vel, max_accel)
        motor.vel = s_curve_velocity(t * sim_dt, start_vel, start_accel, goal_vel, max_accel, max_jerk)
        positions.append(motor.pos)
        velocities.append(motor.vel)
        accelerations.append(motor.accel)

    plt.figure(figsize=(10, 6))
    plt.plot(velocities, label="velocity")
    plt.legend()

    plt.show()
