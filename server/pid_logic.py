"""PID + state-machine line-following logic adapted for race AI."""

from __future__ import annotations


class LineFollowerPID:
    def __init__(self, kp=0.45, kd=0.18, turn_duration=8):
        self.kp = kp
        self.kd = kd
        self.prev_error = 0.0
        self.state = "FOLLOWING"
        self.turn_duration = max(3, int(turn_duration))
        self.turn_counter = 0

    def calculate_pid(self, error):
        if error is None:
            return 0.0, "Line Lost -> fallback stabilize", 0.0, 0.0

        derivative = error - self.prev_error
        p_term = self.kp * error
        d_term = self.kd * derivative
        output = p_term + d_term
        self.prev_error = error

        reasoning = []
        if error > 12:
            reasoning.append("Line center is to the RIGHT.")
        elif error < -12:
            reasoning.append("Line center is to the LEFT.")
        else:
            reasoning.append("Car is near line center.")

        if abs(derivative) > 8:
            if derivative * error > 0:
                reasoning.append("Deviation growing; stronger correction.")
            else:
                reasoning.append("Recovering to center; smooth correction.")

        if output > 0.4:
            reasoning.append("Decision: steer right aggressive.")
        elif output < -0.4:
            reasoning.append("Decision: steer left aggressive.")
        elif output > 0.08:
            reasoning.append("Decision: steer right gentle.")
        elif output < -0.08:
            reasoning.append("Decision: steer left gentle.")
        else:
            reasoning.append("Decision: hold line.")

        return output, " | ".join(reasoning), p_term, d_term

    def update_state(self, horizontal_line_detected, trigger_zone_reached):
        if self.state == "FOLLOWING" and horizontal_line_detected and trigger_zone_reached:
            self.state = "TURNING_90"
            self.turn_counter = 0
            self.prev_error = 0.0
        elif self.state == "TURNING_90":
            self.turn_counter += 1
            if self.turn_counter >= self.turn_duration:
                self.state = "FOLLOWING"
                self.prev_error = 0.0
        return self.state
