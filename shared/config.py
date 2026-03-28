# shared/config.py
"""Central configuration for server endpoints and tunnels."""

import os

# The user can override these via environment variables.
NGROK_URL = os.getenv("ONLINERACER_NGROK_URL", "wss://replace-with-your-id.ngrok-free.app")
FIREBASE_URL = os.getenv("ONLINERACER_FIREBASE_URL", "wss://domoneyracing-default-rtdb.firebaseio.com/.ws")
LOCAL_URL = os.getenv("ONLINERACER_LOCAL_URL", "ws://localhost:8765")

# Priority order: ngrok primary, firebase relay fallback, then local.
ENDPOINTS = [
    NGROK_URL,
    FIREBASE_URL,
    LOCAL_URL,
]
