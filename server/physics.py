"""Server-side race simulation with PID line-following cars."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Dict, List, Tuple

from shared import constants
from server.pid_logic import LineFollowerPID


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def wrap_angle_rad(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


@dataclass
class CarState:
    car_id: str
    label: str
    color: tuple
    lane: int
    base_skill: float
    x: float
    y: float
    heading: float
    speed: float
    lap: int = 0
    last_segment: int = 0
    finished_at: float | None = None
    odds: float = 2.0
    controller: LineFollowerPID | None = None


class RaceEngine:
    def __init__(self):
        self.time_s = 0.0
        self.phase = "COUNTDOWN"
        self.phase_time_s = 0.0
        self.race_no = 1
        self.rigged_winner: str | None = None
        self.notifications: List[dict] = []
        self.cars: List[CarState] = []
        self.paths = self._build_lane_paths()
        self._new_race()

    def set_rigged_winner(self, car_id: str | None):
        self.rigged_winner = car_id

    def clear_rigged_winner(self):
        self.rigged_winner = None

    def _build_lane_paths(self) -> Dict[int, List[Tuple[float, float]]]:
        paths = {}
        for lane in range(constants.LANE_COUNT):
            inset = 20 + lane * 16
            x0 = constants.TRACK_OUTER_X + inset
            y0 = constants.TRACK_OUTER_Y + inset
            x1 = constants.TRACK_OUTER_X + constants.TRACK_OUTER_W - inset
            y1 = constants.TRACK_OUTER_Y + constants.TRACK_OUTER_H - inset
            paths[lane] = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return paths

    def _new_race(self):
        self.phase = "COUNTDOWN"
        self.phase_time_s = 0.0
        self.time_s = 0.0
        self.cars = []

        for i in range(constants.LANE_COUNT):
            path = self.paths[i]
            sx, sy = path[0]
            jitter = i * 5.0
            self.cars.append(
                CarState(
                    car_id=f"car{i+1}",
                    label=f"CAR {i+1}",
                    color=constants.CAR_COLORS[i],
                    lane=i,
                    base_skill=random.uniform(0.9, 1.12),
                    x=sx,
                    y=sy + jitter,
                    heading=0.0,
                    speed=random.uniform(constants.BASE_SPEED * 0.8, constants.BASE_SPEED * 1.15),
                    lap=0,
                    last_segment=0,
                    finished_at=None,
                    odds=2.0,
                    controller=LineFollowerPID(
                        kp=random.uniform(0.38, 0.58),
                        kd=random.uniform(0.14, 0.24),
                        turn_duration=random.randint(6, 11),
                    ),
                )
            )

        self._recompute_odds()
        self.notifications.append({"kind": "race", "text": f"Race #{self.race_no} countdown started."})

    def _recompute_odds(self):
        raw = []
        for c in self.cars:
            sensor_quality = c.controller.kp * 0.6 + c.controller.kd * 0.4
            score = (c.base_skill * 0.75) + (sensor_quality * 0.2) + random.uniform(-0.05, 0.06)
            raw.append(max(0.2, score))

        total = sum(raw) or 1.0
        for c, s in zip(self.cars, raw):
            p = s / total
            fair = 1.0 / max(0.05, p)
            c.odds = round(clamp(fair * random.uniform(0.92, 1.1), 1.2, 18.0), 2)

    def _target_segment(self, car: CarState):
        pts = self.paths[car.lane]
        seg = car.last_segment % 4
        curr = pts[seg]
        nxt = pts[(seg + 1) % 4]
        return seg, curr, nxt

    def _distance_to_line(self, px, py, ax, ay, bx, by):
        abx, aby = bx - ax, by - ay
        apx, apy = px - ax, py - ay
        ab_len2 = abx * abx + aby * aby
        if ab_len2 <= 1e-6:
            return math.hypot(apx, apy), 0.0
        t = clamp((apx * abx + apy * aby) / ab_len2, 0.0, 1.0)
        cx = ax + t * abx
        cy = ay + t * aby
        return math.hypot(px - cx, py - cy), t

    def _advance_one(self, car: CarState, dt: float):
        if car.finished_at is not None:
            return

        seg, curr, nxt = self._target_segment(car)
        tx, ty = nxt
        to_target_x = tx - car.x
        to_target_y = ty - car.y
        distance_to_corner = math.hypot(to_target_x, to_target_y)

        desired_heading = math.atan2(to_target_y, to_target_x)
        heading_err = wrap_angle_rad(desired_heading - car.heading)

        line_dist, line_t = self._distance_to_line(car.x, car.y, curr[0], curr[1], nxt[0], nxt[1])
        line_side = math.sin(car.heading) * to_target_x - math.cos(car.heading) * to_target_y
        signed_line = line_dist if line_side > 0 else -line_dist
        sensor_error = math.degrees(heading_err) * 0.45 + signed_line * 0.15

        horizontal_line_detected = distance_to_corner < 42.0
        trigger_zone_reached = line_t > 0.78 or distance_to_corner < 36.0
        state = car.controller.update_state(horizontal_line_detected, trigger_zone_reached)

        pid_out, _, _, _ = car.controller.calculate_pid(sensor_error)
        steer_gain = 0.018 if state == "FOLLOWING" else 0.028
        car.heading = wrap_angle_rad(car.heading + pid_out * steer_gain)

        target_speed = constants.BASE_SPEED * car.base_skill
        if state == "TURNING_90":
            target_speed *= 0.82
        target_speed += random.uniform(-0.08, 0.12)
        car.speed += (target_speed - car.speed) * 0.13
        car.speed = clamp(car.speed, 1.2, constants.MAX_SPEED)

        car.x += math.cos(car.heading) * car.speed * dt * 60.0
        car.y += math.sin(car.heading) * car.speed * dt * 60.0

        if distance_to_corner < 24.0:
            prev = car.last_segment
            car.last_segment = (car.last_segment + 1) % 4
            if prev == 3 and car.last_segment == 0:
                car.lap += 1
                if car.lap >= constants.LAPS_PER_RACE:
                    car.finished_at = self.time_s
                    self.notifications.append({"kind": "finish", "text": f"{car.label} finished."})

    def _apply_collisions(self):
        for i, a in enumerate(self.cars):
            if a.finished_at is not None:
                continue
            for j in range(i + 1, len(self.cars)):
                b = self.cars[j]
                if b.finished_at is not None:
                    continue
                dist = math.hypot(a.x - b.x, a.y - b.y)
                if dist < constants.COLLISION_DISTANCE:
                    if dist < 1e-6:
                        dist = 1.0
                    nx = (a.x - b.x) / dist
                    ny = (a.y - b.y) / dist
                    push = (constants.COLLISION_DISTANCE - dist) * 0.55
                    a.x += nx * push
                    a.y += ny * push
                    b.x -= nx * push
                    b.y -= ny * push
                    a.speed = max(1.1, a.speed - random.uniform(0.3, 0.8))
                    b.speed = max(1.1, b.speed - random.uniform(0.3, 0.8))
                    if random.random() < 0.25:
                        self.notifications.append(
                            {"kind": "flag", "text": f"Contact: {a.label} vs {b.label}."}
                        )

    def _all_finished(self):
        return all(c.finished_at is not None for c in self.cars)

    def tick(self, dt: float):
        self.phase_time_s += dt
        self.time_s += dt

        if self.phase == "COUNTDOWN":
            if self.phase_time_s >= constants.COUNTDOWN_SECONDS:
                self.phase = "RACING"
                self.phase_time_s = 0.0
                self.notifications.append({"kind": "race", "text": "Race started. Bets locked."})
            return

        if self.phase == "RACING":
            for car in self.cars:
                self._advance_one(car, dt)
            self._apply_collisions()

            if random.random() < 0.05:
                self._recompute_odds()
                self.notifications.append({"kind": "odds", "text": "Live odds recalculated."})

            if self._all_finished():
                self.phase = "POST_RACE"
                self.phase_time_s = 0.0
                self.notifications.append({"kind": "race", "text": "Race ended. Settling wagers."})
            return

        if self.phase == "POST_RACE" and self.phase_time_s >= constants.POST_RACE_PAUSE_SECONDS:
            self.race_no += 1
            self.notifications = []
            self._new_race()

    def consume_notifications(self):
        out = self.notifications[:]
        self.notifications.clear()
        return out

    def get_rankings(self):
        def progress_key(c):
            seg_progress = c.last_segment * 10000
            return c.lap * 100000 + seg_progress

        def rig_bias(c):
            if self.rigged_winner and c.car_id == self.rigged_winner:
                return -1
            return 0

        return sorted(
            self.cars,
            key=lambda c: (
                rig_bias(c),
                c.finished_at if c.finished_at is not None else 1e9,
                -progress_key(c),
            ),
        )

    def snapshot(self):
        ranking = self.get_rankings()
        ranking_payload = [
            {
                "place": i + 1,
                "car_id": c.car_id,
                "name": c.label,
                "lap": c.lap,
                "odds": c.odds,
                "finished": c.finished_at is not None,
            }
            for i, c in enumerate(ranking)
        ]

        cars_payload = [
            {
                "id": c.car_id,
                "name": c.label,
                "x": round(c.x, 2),
                "y": round(c.y, 2),
                "lap": c.lap,
                "odds": c.odds,
                "finished": c.finished_at is not None,
                "color": list(c.color),
            }
            for c in self.cars
        ]

        return {
            "phase": self.phase,
            "phase_time": round(self.phase_time_s, 2),
            "race_no": self.race_no,
            "cars": cars_payload,
            "rankings": ranking_payload,
            "laps_per_race": constants.LAPS_PER_RACE,
            "rigged_winner": self.rigged_winner,
        }
