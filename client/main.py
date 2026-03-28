# client/main.py
"""Main async game loop for the rebuilt online wager racer."""

import asyncio

import pygame

from shared import constants
from client.networking import ConnectionManager
from client.rendering import Renderer
from client.ui import UIManager


class GameClient:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(constants)
        self.ui = UIManager()
        self.network = ConnectionManager(self)

        self.server_state = {}
        self.local_player_id = None
        self.connected_uri = None

        self.chat_events = []
        self.notifications = []
        self.sentiment_text = "Waiting for crowd signal"
        self.leaderboard = []

    def wallet_for_local_player(self):
        if not self.local_player_id:
            return None
        for item in self.server_state.get("wallets", []):
            if item.get("player_id") == self.local_player_id:
                return item
        return None

    def push_notification(self, text):
        self.notifications.append({"kind": "system", "text": str(text)})
        self.notifications = self.notifications[-20:]

    def on_connected(self, uri):
        self.connected_uri = uri
        self.push_notification(f"Connected to {uri}")

    def on_disconnected(self):
        self.connected_uri = None

    def on_room_state(self, state):
        self.server_state = state or {}

    def on_leaderboard(self, data):
        self.leaderboard = data or []

    def on_chat_event(self, event):
        if event:
            self.chat_events.append(event)
            self.chat_events = self.chat_events[-40:]

    def on_sentiment(self, payload):
        self.sentiment_text = payload.get("text", "")

    def on_notification(self, payload):
        if payload:
            self.notifications.append(payload)
            self.notifications = self.notifications[-20:]

    def on_bet_result(self, payload):
        message = payload.get("message", "Bet update") if payload else "Bet update"
        self.push_notification(message)

    def on_race_result(self, payload):
        if not payload:
            return
        sign = "+" if payload.get("delta", 0) >= 0 else ""
        self.notifications.append(
            {
                "kind": "settlement",
                "text": f"{payload.get('player')}: {sign}{payload.get('delta', 0)} -> ${payload.get('money', 0)}",
            }
        )
        self.notifications = self.notifications[-20:]

    async def ensure_connection_and_join(self):
        connected = await self.network.connect()
        if connected:
            self.network.join_room(self.ui.room_text, self.ui.name_text)
        else:
            self.push_notification("Could not connect using ngrok/firebase/local endpoints.")

    async def main_loop(self):
        running = True
        await self.ensure_connection_and_join()

        while running:
            self.clock.tick(constants.FPS)
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    break

                actions = self.ui.handle_event(event)
                for action in actions:
                    kind = action.get("type")
                    if kind == "join":
                        await self.ensure_connection_and_join()
                    elif kind == "bet":
                        self.network.place_bet(action["car_id"], action["amount"])
                    elif kind == "coupon":
                        self.network.redeem_coupon(action["code"])
                    elif kind == "chat_send":
                        text = action.get("text", "").strip()
                        if text:
                            self.network.send_chat(text)

            self.ui.draw(
                self.renderer.screen,
                self.server_state,
                self.chat_events,
                self.leaderboard,
                self.sentiment_text,
                self.notifications,
                self.wallet_for_local_player(),
                self.connected_uri,
            )
            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()
