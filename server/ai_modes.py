"""Lightweight AI helpers for chat strategist and live sentiment."""

from __future__ import annotations

from collections import deque
import random
import re
from typing import Deque, Dict, Iterable, List

BULLISH_WORDS = {"win", "favorite", "hot", "strong", "best", "lock", "safe", "easy"}
BEARISH_WORDS = {"fade", "weak", "bad", "cold", "slow", "avoid", "risky"}


class ChatStrategist:
    def __init__(self):
        self.recent: Deque[str] = deque(maxlen=60)

    def append_user_text(self, text: str):
        self.recent.append(text.lower())

    def build_reply(self, question: str, cars: Iterable[dict], ranking: Iterable[dict]) -> str:
        q = question.lower()
        car_list = list(cars)
        ranking_list = list(ranking)

        if "help" in q:
            return (
                "Try: 'exacta', 'longshot', 'odds', 'strategist track'. "
                "Exacta = top-2 order idea, Longshot = highest-odds value play, "
                "Odds = current market board."
            )

        if "exacta" in q:
            top_two = ranking_list[:2]
            if len(top_two) >= 2:
                return f"Exacta lean: {top_two[0]['name']} over {top_two[1]['name']}. Hedge with a reverse exacta for volatility." 
            return "Need a live board to suggest an exacta."

        if "longshot" in q:
            if not car_list:
                return "No car data available yet for longshot analysis."
            best = max(car_list, key=lambda c: c.get("odds", 1.0))
            return f"Longshot call: {best['name']} at {best.get('odds', 0):.2f} odds. Use a small stake only."

        if "track" in q or "condition" in q or "pit" in q or "history" in q:
            leader = ranking_list[0]["name"] if ranking_list else "CAR 1"
            return (
                f"Track strategist: inside lanes are cleaner today, but contact risk is high in corners. "
                f"Current flow favors {leader}. Watch for yellow-flag style slowdowns after collisions."
            )

        if "data" in q or "odds" in q or "who" in q:
            short = ", ".join([f"{c['name']} ({c.get('odds', 0):.2f})" for c in car_list[:5]])
            return f"Live board snapshot: {short}."

        generic_tips = [
            "Split stake across win + place when the board is unstable.",
            "If chat sentiment crowds one car, look for value on the second favorite.",
            "Wait for one odds refresh before entering a larger bet.",
        ]
        return f"AI strategist: {random.choice(generic_tips)}"


class SentimentTracker:
    def __init__(self):
        self.window: Deque[str] = deque(maxlen=80)

    def push(self, text: str):
        self.window.append(text.lower())

    def summarize(self) -> Dict[str, int]:
        counts = {f"car{i}": 0 for i in range(1, 6)}
        for line in self.window:
            for i in range(1, 6):
                if f"car {i}" in line or f"car{i}" in line:
                    bias = 1
                    if any(w in line for w in BULLISH_WORDS):
                        bias += 1
                    if any(w in line for w in BEARISH_WORDS):
                        bias -= 1
                    counts[f"car{i}"] += bias
        return counts

    def trend_message(self) -> str:
        data = self.summarize()
        top = max(data.items(), key=lambda kv: kv[1])
        if top[1] <= 0:
            return "Crowd sentiment is mixed, no clear favorite right now."
        car_id = re.sub(r"car", "CAR ", top[0]).upper()
        return f"Sentiment shift: crowd confidence is moving toward {car_id}."
