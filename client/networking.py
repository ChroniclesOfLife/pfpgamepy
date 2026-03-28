"""Client networking with Firebase -> ngrok -> local fallback."""

import asyncio

import websockets

from shared import config, protocol


class ConnectionManager:
    def __init__(self, app):
        self.app = app
        self.ws = None
        self.current_uri = None

    async def connect(self):
        for uri in config.ENDPOINTS:
            if not isinstance(uri, str) or not uri.startswith("ws"):
                continue
            try:
                self.ws = await asyncio.wait_for(
                    websockets.connect(uri, ping_interval=20, ping_timeout=20),
                    timeout=4.5,
                )
                self.current_uri = uri
                self.app.on_connected(uri)
                asyncio.create_task(self.listen_loop())
                return True
            except Exception as exc:
                self.app.push_notification(f"Connect failed: {uri} ({exc})")
        return False

    async def listen_loop(self):
        try:
            async for message in self.ws:
                msg_type, payload = protocol.unpack_msg(message)
                if msg_type == protocol.MsgType.GAME_START:
                    self.app.local_player_id = payload.get("id")
                elif msg_type == protocol.MsgType.ROOM_STATE:
                    self.app.on_room_state(payload)
                elif msg_type == protocol.MsgType.LEADERBOARD_UPDATE:
                    self.app.on_leaderboard(payload)
                elif msg_type == protocol.MsgType.CHAT_EVENT:
                    self.app.on_chat_event(payload)
                elif msg_type == protocol.MsgType.SENTIMENT_UPDATE:
                    self.app.on_sentiment(payload)
                elif msg_type == protocol.MsgType.NOTIFICATION:
                    self.app.on_notification(payload)
                elif msg_type == protocol.MsgType.BET_RESULT:
                    self.app.on_bet_result(payload)
                elif msg_type == protocol.MsgType.RACE_RESULT:
                    self.app.on_race_result(payload)
        except websockets.exceptions.ConnectionClosed:
            self.app.push_notification("Disconnected from server.")
        finally:
            self.app.on_disconnected()

    def _send(self, msg_type, payload):
        if self.ws:
            raw = protocol.pack_msg(msg_type, payload)
            asyncio.create_task(self.ws.send(raw))

    def join_room(self, room_id, name):
        self._send(protocol.MsgType.JOIN_ROOM, {"room_id": room_id, "name": name})

    def place_bet(self, car_id, amount):
        self._send(protocol.MsgType.PLACE_BET, {"car_id": car_id, "amount": int(amount)})

    def send_chat(self, message):
        self._send(protocol.MsgType.CHAT_SEND, {"message": message})

    def redeem_coupon(self, code):
        self._send(protocol.MsgType.REDEEM_COUPON, {"code": code})
