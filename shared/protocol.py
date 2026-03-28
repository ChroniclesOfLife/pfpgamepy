# shared/protocol.py
import json

class MsgType:
    # Client -> Server
    JOIN_ROOM = "JOIN_ROOM"
    PLACE_BET = "PLACE_BET"
    CANCEL_BET = "CANCEL_BET"
    CHAT_SEND = "CHAT_SEND"
    REDEEM_COUPON = "REDEEM_COUPON"
    ADMIN_ACTION = "ADMIN_ACTION"

    # Server -> Client
    ROOM_STATE = "ROOM_STATE"
    GAME_START = "GAME_START"
    RACE_RESULT = "RACE_RESULT"
    LEADERBOARD_UPDATE = "LEADERBOARD_UPDATE"
    CHAT_EVENT = "CHAT_EVENT"
    SENTIMENT_UPDATE = "SENTIMENT_UPDATE"
    NOTIFICATION = "NOTIFICATION"
    BET_RESULT = "BET_RESULT"
    ADMIN_RESULT = "ADMIN_RESULT"
    ERROR = "ERROR"

def pack_msg(msg_type, payload):
    return json.dumps({"type": msg_type, "payload": payload})

def unpack_msg(raw_str):
    try:
        data = json.loads(raw_str)
        return data.get("type"), data.get("payload")
    except Exception:
        return None, None
