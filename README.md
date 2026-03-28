# PFPGamePy / DoMoneyRacing

Browser-based racing simulation with live odds, wallet/betting flow, queue/cancel wagers, coupon effects, AI chat strategist, live sentiment, and multiplayer room support over WebSocket.

## Important Legal Notice

### English
This repository is for educational and demonstration purposes only. It is not a real-money gambling platform.
By using this software, you accept all risk. The authors/contributors provide this project "as is" with no warranty and no liability for losses, damages, legal issues, or decisions made from simulation output.

### Tuyen bo mien tru trach nhiem (Tieng Viet)
Du an nay chi phuc vu muc dich hoc tap, nghien cuu va mo phong. Day khong phai nen tang ca cuoc tien that.
Khi su dung phan mem, ban tu chiu moi rui ro. Tac gia/contributor khong chiu trach nhiem doi voi bat ky ton that, thiet hai, van de phap ly, hoac quyet dinh nao dua tren ket qua mo phong.

## Consent Requirement in App

The web client now starts with a mandatory consent overlay:

1. Confirm educational/simulation-only purpose.
2. Confirm age 18+ and consent.

Until both are accepted, gameplay/connection remains locked.

## Deployment Notice

The deployed GitHub Pages build (if present in this repository) should be treated as an earlier preview and not stable.
For the latest behavior, use the current Firebase Hosting deployment and run the latest backend from this repository.

## Features

1. Top-down nested-rectangle race with 5 AI cars and collision events.
2. Dynamic live odds and race-by-race settlement.
3. Wallet system with queue/cancel bet flow.
4. Coupon mechanics:
  - `DOMONEY` (loan from bank)
  - `TROIDO` (loan sharks)
  - `KHONGDO` (charity)
  - `DOHAYKHONGDO` (50/50)
5. Ask-AI chat strategist and live sentiment updates.
6. Live room leaderboard + all-time leaderboard.
7. Rich overlays: countdown, winner, collision/alert fades.
8. Endpoint selector with priority order and failover status colors.

## Quick Start (Local Host)

1. Install dependencies.

```bash
pip install -r requirements.txt
```

2. Run backend.

```bash
python run_server.py
```

3. Open the hosted web client and connect using your endpoint list.

## Multi-Computer Access (Recommended)

1. Start backend on host machine:

```bash
python run_server.py
```

2. Expose via ngrok:

```bash
ngrok http 8765
```

3. Use ngrok websocket endpoint in clients:
  - `wss://<your-ngrok-host>`

4. In web UI, set this endpoint as `FIRST`.

## Endpoint Notes

1. `wss://<ngrok-host>` is primary for remote users.
2. Firebase `.ws` endpoint is fallback only if you run a compatible relay.
3. `ws://localhost:8765` works only on the same machine as backend.

## Betting and Payout Formulas

Definitions:

1. `gross_payout = bet_amount x live_odds x payout_multiplier`
2. `house_fee = gross_payout x house_takeout`
3. `payout_after_takeout = gross_payout - house_fee`
4. Win net change: `net_change = payout_after_takeout - bet_amount`
5. Loss net change: `net_change = -bet_amount`

Current default values:

1. Starting money: `$1000`
2. Bet range: `$10 .. $500`
3. House takeout: `8%`

Worked example:

1. Bet `$100` on CAR3.
2. Live odds `3.40`, multiplier `2.00`.
3. Gross payout: `100 x 3.40 x 2.00 = 680`.
4. House fee: `680 x 0.08 = 54.4`.
5. After takeout: about `626` (server rounding applies).
6. Net wallet change: `626 - 100 = +526`.

## Live Odds Model (High Level)

1. Each car receives a changing performance score.
2. Scores are normalized into probabilities.
3. Fair decimal odds are `1 / probability`.
4. A small market variance factor is applied and clamped.
5. Odds update live as race state evolves.

Approximate interpretation:

1. Odds `5.00` implies about `1/5 = 20%` chance.
2. Odds move over time; this is simulation, not bookmaker pricing.

## Project Layout

1. Frontend:
  - `firebase_hosting/index.html`
  - `firebase_hosting/styles.css`
  - `firebase_hosting/app.js`
2. Backend:
  - `server/server.py`
  - `server/rooms.py`
  - `server/physics.py`
  - `server/ai_modes.py`
  - `server/leaderboard.py`
3. Shared protocol/config:
  - `shared/protocol.py`
  - `shared/config.py`
  - `shared/constants.py`

## Troubleshooting

### Stuck on WAITING / cannot join

1. Ensure backend is running on host:
  - `python run_server.py`
2. Ensure ngrok is active:
  - `ngrok http 8765`
3. Use public `wss://` endpoint on other networks.
4. Hard refresh browser (`Ctrl+F5`).

### Port 8765 already in use

1. Stop process using port 8765.
2. Restart backend.

### Firebase endpoint closes immediately

This is expected if no compatible websocket relay is configured. Keep ngrok endpoint first.
