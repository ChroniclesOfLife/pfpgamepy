# server/server.py
"""Asyncio WebSocket game server with 60Hz physics tick loop."""
import asyncio
import websockets

from shared.protocol import MsgType, pack_msg, unpack_msg
from shared.constants import SERVER_TICK_RATE
from server.rooms import RoomManager
from server.leaderboard import Leaderboard
from server.tunnel_helper import print_tunnel_instructions

leaderboard = Leaderboard()
room_manager = RoomManager(leaderboard)


def _safe_top_10():
    try:
        return leaderboard.get_top_10()
    except Exception as exc:
        print(f"[WARN] leaderboard read failed: {exc}")
        return []


async def handle_client(websocket):
    """Per-connection handler."""
    current_room = None
    player_id = str(id(websocket))

    try:
        async for message in websocket: 
            msg_type, payload = unpack_msg(message)
            payload = payload or {}

            if msg_type == MsgType.JOIN_ROOM:
                room_id = payload.get("room_id", "Lobby1")
                name = payload.get("name", "Player")
                if current_room:
                    current_room.remove_client(websocket)
                current_room = room_manager.get_or_create_room(room_id)
                current_room.add_client(websocket, player_id, name)
                await websocket.send(pack_msg(MsgType.GAME_START, {"id": player_id}))
                await websocket.send(pack_msg(MsgType.LEADERBOARD_UPDATE, _safe_top_10()))

            elif msg_type == MsgType.PLACE_BET and current_room:
                ok, message = current_room.place_bet(
                    player_id=player_id,
                    car_id=payload.get("car_id", "car1"),
                    amount=int(payload.get("amount", 0)),
                    queue_next=bool(payload.get("queue_next", False)),
                )
                await websocket.send(pack_msg(MsgType.BET_RESULT, {"ok": ok, "message": message}))

            elif msg_type == MsgType.CANCEL_BET and current_room:
                ok, message = current_room.cancel_bet(player_id=player_id)
                await websocket.send(pack_msg(MsgType.BET_RESULT, {"ok": ok, "message": message}))

            elif msg_type == MsgType.CHAT_SEND and current_room:
                events = current_room.add_chat(player_id, payload.get("message", ""))
                for event in events:
                    msg = pack_msg(MsgType.CHAT_EVENT, event)
                    await asyncio.gather(*[ws.send(msg) for ws in list(current_room.clients)], return_exceptions=True)

            elif msg_type == MsgType.REDEEM_COUPON and current_room:
                ok, message, delta = current_room.redeem_coupon(player_id, payload.get("code", ""))
                await websocket.send(pack_msg(MsgType.NOTIFICATION, {"kind": "coupon", "ok": ok, "delta": delta, "text": message}))

            elif msg_type == MsgType.ADMIN_ACTION and current_room:
                action = payload.get("action", "")
                ok, message = current_room.admin_action(action, payload)
                await websocket.send(pack_msg(MsgType.ADMIN_RESULT, {"ok": ok, "message": message, "action": action}))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if current_room:
            current_room.remove_client(websocket)
            room_manager.remove_empty_rooms()


async def physics_tick_loop():
    """Authoritative tick + broadcast."""
    tick_time = 1.0 / SERVER_TICK_RATE
    loop = asyncio.get_event_loop()

    while True:
        t0 = loop.time()

        for room in list(room_manager.rooms.values()):
            if room.is_empty():
                continue
            events = room.tick(tick_time)

            snapshot = room.build_state()
            state_msg = pack_msg(MsgType.ROOM_STATE, snapshot)
            coros = [ws.send(state_msg) for ws in list(room.clients)]
            if coros:
                await asyncio.gather(*coros, return_exceptions=True)

            for n in events.get("engine_notifications", []):
                msg = pack_msg(MsgType.NOTIFICATION, n)
                await asyncio.gather(*[ws.send(msg) for ws in list(room.clients)], return_exceptions=True)

            for n in events.get("room_notifications", []):
                msg = pack_msg(MsgType.NOTIFICATION, n)
                await asyncio.gather(*[ws.send(msg) for ws in list(room.clients)], return_exceptions=True)

            sentiment = events.get("sentiment")
            if sentiment:
                msg = pack_msg(MsgType.SENTIMENT_UPDATE, {"text": sentiment})
                await asyncio.gather(*[ws.send(msg) for ws in list(room.clients)], return_exceptions=True)

            settlements = events.get("settlements", [])
            for item in settlements:
                msg = pack_msg(MsgType.RACE_RESULT, item)
                await asyncio.gather(*[ws.send(msg) for ws in list(room.clients)], return_exceptions=True)

            lb_msg = pack_msg(MsgType.LEADERBOARD_UPDATE, _safe_top_10())
            await asyncio.gather(*[ws.send(lb_msg) for ws in list(room.clients)], return_exceptions=True)

        elapsed = loop.time() - t0
        await asyncio.sleep(max(0, tick_time - elapsed))


async def main():
    print_tunnel_instructions()
    print(f"Starting server on ws://0.0.0.0:8765  ({SERVER_TICK_RATE} Hz)")
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        await physics_tick_loop()


if __name__ == "__main__":
    asyncio.run(main())
