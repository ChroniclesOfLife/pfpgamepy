# server/tunnel_helper.py
"""Tools to help set up ngrok and Firebase fallback endpoints."""

def print_tunnel_instructions():
    print("\n" + "="*50)
    print("ONLINE HOSTING INSTRUCTIONS")
    print("="*50)
    print("To allow others to join, expose ws://localhost:8765.")
    print("\n1. NGROK (Primary):")
    print("   Run: ngrok http 8765")
    print("   Copy forwarding URL and set ONLINERACER_NGROK_URL=wss://<id>.ngrok-free.app")
    print("\n2. FIREBASE (Fallback endpoint in config):")
    print("   Set ONLINERACER_FIREBASE_URL=wss://<project>-default-rtdb.firebaseio.com/.ws")
    print("   Use this only if ngrok is unavailable and your Firebase websocket relay is configured.")
    print("\n3. LOCAL (always available):")
    print("   Keep ONLINERACER_LOCAL_URL=ws://localhost:8765")
    print("="*50 + "\n")

if __name__ == "__main__":
    print_tunnel_instructions()
