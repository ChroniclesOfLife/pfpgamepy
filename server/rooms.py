"""Room management with race, betting, chat AI, and sentiment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import os
import random

from shared import constants
from server.ai_modes import ChatStrategist, SentimentTracker
from server.physics import RaceEngine


VALID_CARS = {"car1", "car2", "car3", "car4", "car5"}

COUPON_VALUES = {
    "DOMONEY": 180,
    "TROIDO": 260,
    "KHONGDO": -180,
}

COUPON_LIMITS = {
    "DOMONEY": 3,
    "TROIDO": 3,
    "KHONGDO": 3,
    "DOHAYKHONGDO": 1,
}


@dataclass
class PlayerProfile:
    player_id: str
    name: str
    money: int = constants.STARTING_MONEY
    wins: int = 0
    streak: int = 0
    badges: List[str] = field(default_factory=list)
    active_bet: dict | None = None
    queued_bet: dict | None = None
    coupon_uses: Dict[str, int] = field(default_factory=dict)


class Room:
    def __init__(self, room_id: str, leaderboard):
        self.room_id = room_id
        self.leaderboard = leaderboard
        self.engine = RaceEngine()
        self.admin_token = os.getenv("DOMONEY_ADMIN_TOKEN", "admin123")
        self.payout_multiplier = 1.0
        self.clients = set()
        self.client_to_player: Dict[object, str] = {}
        self.players: Dict[str, PlayerProfile] = {}

        self.chat_log: List[dict] = []
        self.notifications: List[dict] = []
        self.strategist = ChatStrategist()
        self.sentiment = SentimentTracker()

        self.last_sentiment_push = 0.0
        self.settled_race_no = 0

    def add_client(self, ws, player_id: str, name: str):
        self.clients.add(ws)
        self.client_to_player[ws] = player_id
        if player_id not in self.players:
            self.players[player_id] = PlayerProfile(player_id=player_id, name=name)
        else:
            self.players[player_id].name = name
        self.notifications.append({"kind": "system", "text": f"{name} joined room {self.room_id}."})

    def remove_client(self, ws):
        if ws in self.clients:
            self.clients.discard(ws)
            self.client_to_player.pop(ws, None)

    def is_empty(self):
        return len(self.clients) == 0

    def place_bet(self, player_id: str, car_id: str, amount: int, queue_next: bool = False) -> tuple[bool, str]:
        profile = self.players.get(player_id)
        if not profile:
            return False, "Unknown player"

        car_id = str(car_id).lower().strip()
        if car_id not in VALID_CARS:
            return False, "Invalid car selection"

        try:
            amount = int(amount)
        except Exception:
            return False, "Amount must be a number"

        if amount < constants.MIN_BET or amount > constants.MAX_BET:
            return False, f"Bet must be between {constants.MIN_BET} and {constants.MAX_BET}"

        if amount > profile.money:
            return False, "Not enough money"

        if self.engine.phase == "COUNTDOWN" and not queue_next:
            profile.active_bet = {"car_id": car_id, "amount": amount, "race_no": self.engine.race_no}
            self.notifications.append(
                {
                    "kind": "bet",
                    "text": f"{profile.name} bet ${amount} on {car_id.upper()} for race #{self.engine.race_no}.",
                }
            )
            return True, f"Bet accepted for race #{self.engine.race_no}"

        profile.queued_bet = {"car_id": car_id, "amount": amount, "race_no": self.engine.race_no + 1}
        self.notifications.append(
            {
                "kind": "bet",
                "text": f"{profile.name} queued ${amount} on {car_id.upper()} for race #{self.engine.race_no + 1}.",
            }
        )
        return True, f"Bet queued for race #{self.engine.race_no + 1}"

    def cancel_bet(self, player_id: str) -> tuple[bool, str]:
        profile = self.players.get(player_id)
        if not profile:
            return False, "Unknown player"

        if self.engine.phase == "COUNTDOWN" and profile.active_bet and profile.active_bet.get("race_no") == self.engine.race_no:
            profile.active_bet = None
            self.notifications.append({"kind": "bet", "text": f"{profile.name} canceled current-race bet."})
            return True, "Current race bet canceled"

        if profile.queued_bet:
            profile.queued_bet = None
            self.notifications.append({"kind": "bet", "text": f"{profile.name} canceled queued bet."})
            return True, "Queued bet canceled"

        return False, "No cancelable bet found"

    def redeem_coupon(self, player_id: str, code: str) -> tuple[bool, str, int]:
        profile = self.players.get(player_id)
        if not profile:
            return False, "Unknown player", 0

        key = str(code).strip().upper()
        limit = COUPON_LIMITS.get(key)
        if limit is None:
            return False, "Invalid coupon", 0

        used = int(profile.coupon_uses.get(key, 0))
        if used >= limit:
            return False, f"Coupon limit reached ({used}/{limit})", 0

        if key == "DOHAYKHONGDO":
            delta = random.choice([220, -220])
        else:
            delta = COUPON_VALUES[key]

        profile.money += delta
        profile.coupon_uses[key] = used + 1

        text = f"{profile.name} redeemed {key}: {delta:+d}. Uses {profile.coupon_uses[key]}/{limit}."
        self.notifications.append({"kind": "coupon", "text": text})
        return True, text, delta

    def add_chat(self, player_id: str, message: str) -> List[dict]:
        profile = self.players.get(player_id)
        if not profile:
            return []

        clean = str(message).strip()
        if not clean:
            return []

        chat_events = [{"sender": profile.name, "message": clean, "kind": "player"}]
        self.chat_log.append(chat_events[0])
        self.strategist.append_user_text(clean)
        self.sentiment.push(clean)

        lower = clean.lower()
        if lower.startswith("/ai") or "exacta" in lower or "longshot" in lower or "strategist" in lower:
            snap = self.engine.snapshot()
            ai_reply = self.strategist.build_reply(clean, snap["cars"], snap["rankings"])
            event = {"sender": "WagersBot", "message": ai_reply, "kind": "ai"}
            chat_events.append(event)
            self.chat_log.append(event)

        return chat_events

    def admin_action(self, action: str, payload: dict) -> tuple[bool, str]:
        token = str(payload.get("token", ""))
        if token != self.admin_token:
            return False, "Admin token invalid"

        act = str(action).strip().lower()

        if act == "set_rig_winner":
            car_id = str(payload.get("car_id", "")).lower().strip()
            if car_id not in VALID_CARS:
                return False, "Invalid car id"
            self.engine.set_rigged_winner(car_id)
            self.notifications.append({"kind": "admin", "text": f"Admin rigged winner set to {car_id.upper()}."})
            return True, f"Rigged winner -> {car_id.upper()}"

        if act == "clear_rig":
            self.engine.clear_rigged_winner()
            self.notifications.append({"kind": "admin", "text": "Admin cleared rigged winner."})
            return True, "Rigging cleared"

        if act == "set_multiplier":
            try:
                value = float(payload.get("value", 1.0))
            except Exception:
                return False, "Multiplier must be a number"
            value = max(0.5, min(5.0, value))
            self.payout_multiplier = value
            self.notifications.append({"kind": "admin", "text": f"Admin set payout multiplier to x{value:.2f}."})
            return True, f"Multiplier set to x{value:.2f}"

        if act == "adjust_player_money":
            target_name = str(payload.get("player_name", "")).strip()
            if not target_name:
                return False, "Player name required"

            try:
                delta = int(payload.get("delta", 0))
            except Exception:
                return False, "Delta must be integer"

            target = None
            for p in self.players.values():
                if p.name.lower() == target_name.lower():
                    target = p
                    break

            if not target:
                return False, "Player not found in room"

            target.money += delta
            self.notifications.append({"kind": "admin", "text": f"Admin adjusted {target.name} money by {delta:+d}."})
            return True, f"{target.name} money adjusted by {delta:+d}"

        return False, "Unknown admin action"

    def consume_notifications(self) -> List[dict]:
        out = self.notifications[:]
        self.notifications.clear()
        return out

    def _activate_queued_bets(self):
        if self.engine.phase != "COUNTDOWN":
            return

        for profile in self.players.values():
            queued = profile.queued_bet
            if not queued:
                continue
            if queued.get("race_no") != self.engine.race_no:
                continue

            amount = int(queued.get("amount", 0))
            if amount > profile.money:
                profile.queued_bet = None
                self.notifications.append(
                    {
                        "kind": "bet",
                        "text": f"{profile.name} queued bet dropped (insufficient money).",
                    }
                )
                continue

            profile.active_bet = queued
            profile.queued_bet = None
            self.notifications.append(
                {
                    "kind": "bet",
                    "text": f"{profile.name} queued bet is now active on {profile.active_bet['car_id'].upper()} ${profile.active_bet['amount']}",
                }
            )

    def _settle_race_if_needed(self):
        if self.engine.phase != "POST_RACE":
            return []
        if self.settled_race_no == self.engine.race_no:
            return []

        results = []
        ranking = self.engine.get_rankings()
        winner = ranking[0].car_id if ranking else "car1"

        for profile in self.players.values():
            bet = profile.active_bet
            if not bet or bet.get("race_no") != self.engine.race_no:
                profile.active_bet = None
                continue

            amount = int(bet.get("amount", 0))
            if amount <= 0:
                profile.active_bet = None
                continue

            if bet.get("car_id") == winner:
                odds = next((c.odds for c in ranking if c.car_id == winner), 2.0)
                gross_payout = float(amount) * float(odds) * float(self.payout_multiplier)
                house_fee = int(round(gross_payout * constants.HOUSE_TAKEOUT))
                payout_after_takeout = int(round(gross_payout)) - house_fee
                delta = payout_after_takeout - amount
                profile.money += delta
                profile.wins += 1
                profile.streak += 1
                if profile.streak >= 3 and "Hot Streak" not in profile.badges:
                    profile.badges.append("Hot Streak")
                self.leaderboard.record_result(profile.name, delta, True)
                results.append(
                    {
                        "player": profile.name,
                        "win": True,
                        "winner": winner,
                        "delta": delta,
                        "money": profile.money,
                        "amount": amount,
                        "odds": odds,
                        "multiplier": self.payout_multiplier,
                        "house_takeout": constants.HOUSE_TAKEOUT,
                        "house_fee": house_fee,
                        "gross_payout": int(round(gross_payout)),
                        "payout": payout_after_takeout,
                        "formula": f"({amount} x {odds:.2f} x {self.payout_multiplier:.2f}) - house {constants.HOUSE_TAKEOUT * 100:.1f}%",
                    }
                )
            else:
                delta = -amount
                profile.money += delta
                profile.streak = 0
                self.leaderboard.record_result(profile.name, delta, False)
                results.append(
                    {
                        "player": profile.name,
                        "win": False,
                        "winner": winner,
                        "delta": delta,
                        "money": profile.money,
                        "amount": amount,
                        "odds": 0,
                        "multiplier": self.payout_multiplier,
                        "house_takeout": constants.HOUSE_TAKEOUT,
                        "house_fee": 0,
                        "gross_payout": 0,
                        "payout": 0,
                        "formula": f"loss = -{amount}",
                    }
                )

            profile.active_bet = None

        self.settled_race_no = self.engine.race_no
        return results

    def tick(self, dt: float):
        self._activate_queued_bets()
        self.engine.tick(dt)

        random_alerts = [
            "Yellow-flag style slowdown risk in next corner.",
            "Live odds spike detected on lane 3.",
            "Momentum shift: watch split times now.",
        ]
        if random.random() < 0.01:
            self.notifications.append({"kind": "alert", "text": random.choice(random_alerts)})

        self.last_sentiment_push += dt
        sentiment_message = None
        if self.last_sentiment_push >= 6.0:
            self.last_sentiment_push = 0.0
            sentiment_message = self.sentiment.trend_message()

        settlements = self._settle_race_if_needed()
        if settlements:
            self.notifications.append({"kind": "settlement", "text": "Wagers settled for completed race."})

        return {
            "sentiment": sentiment_message,
            "settlements": settlements,
            "engine_notifications": self.engine.consume_notifications(),
            "room_notifications": self.consume_notifications(),
        }

    def build_state(self) -> dict:
        engine_state = self.engine.snapshot()
        live_players = sorted(
            [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "money": p.money,
                    "wins": p.wins,
                    "streak": p.streak,
                    "badges": p.badges,
                }
                for p in self.players.values()
            ],
            key=lambda x: (-x["money"], -x["wins"], x["name"].lower()),
        )

        return {
            **engine_state,
            "wallets": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "money": p.money,
                    "wins": p.wins,
                    "streak": p.streak,
                    "badges": p.badges,
                    "active_bet": p.active_bet,
                    "queued_bet": p.queued_bet,
                    "coupon_uses": p.coupon_uses,
                }
                for p in self.players.values()
            ],
            "live_players": live_players,
            "payout_multiplier": self.payout_multiplier,
            "house_takeout": constants.HOUSE_TAKEOUT,
            "room_id": self.room_id,
        }


class RoomManager:
    def __init__(self, leaderboard):
        self.leaderboard = leaderboard
        self.rooms: Dict[str, Room] = {}

    def get_or_create_room(self, room_id):
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id, self.leaderboard)
        return self.rooms[room_id]

    def remove_empty_rooms(self):
        for r_id in [k for k, v in self.rooms.items() if v.is_empty()]:
            del self.rooms[r_id]
