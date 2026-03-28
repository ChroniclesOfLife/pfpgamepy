# PFPGamePy / DoMoneyRacing

Browser-based racing simulation with live odds, wallet/betting flow, queue/cancel wagers, coupon effects, AI chat strategist, live sentiment, and multiplayer room support over WebSocket.

## Important Legal Notice / Cảnh báo pháp lý quan trọng

### English
This repository is for educational and demonstration purposes only. It is **not** a real-money gambling platform.
By using this software, you accept all risk. The authors/contributors provide this project "as is" with no warranty and no liability for losses, damages, legal issues, or decisions made from simulation output.

Additional usage restrictions and warnings:

1. No real-world money, real-world currency, cash-equivalent value, or redeemable credits may be used with this software.
2. This project must not be used to advertise, promote, or operate real betting/gambling services.
3. Intended for adults only: users must be **18+**.
4. You are responsible for compliance with local laws, platform policies, and age restrictions in your jurisdiction.
5. This project does not provide financial, legal, betting, or investment advice.

### Tuyên bố miễn trừ trách nhiệm (Tiếng Việt)
Dự án này chỉ phục vụ mục đích học tập, nghiên cứu và mô phỏng. Đây **không** phải nền tảng cá cược tiền thật.
Khi sử dụng phần mềm, bạn tự chịu mọi rủi ro. Tác giả/contributor không chịu trách nhiệm đối với bất kỳ tổn thất, thiệt hại, vấn đề pháp lý, hoặc quyết định nào dựa trên kết quả mô phỏng.

Cảnh báo và giới hạn sử dụng bổ sung:

1. Không được sử dụng tiền thật, tiền tệ ngoài đời thực, giá trị quy đổi thành tiền, hoặc điểm có thể quy đổi.
2. Không được dùng dự án này để quảng cáo, thúc đẩy, hoặc vận hành dịch vụ cá cược/đánh bạc thực tế.
3. Chỉ dành cho người trưởng thành: người dùng phải **từ 18 tuổi trở lên**.
4. Người dùng tự chịu trách nhiệm tuân thủ pháp luật địa phương, chính sách nền tảng, và quy định độ tuổi tại nơi sử dụng.
5. Dự án không cung cấp lời khuyên tài chính, pháp lý, cá cược, hay đầu tư.

## Consent Requirement in App

The web client now starts with a mandatory consent overlay:

1. Confirm educational/simulation-only purpose.
2. Confirm age 18+ and consent.

Until both are accepted, gameplay/connection remains locked.

## Deployment Notice

The deployed GitHub Pages build (if present in this repository) should be treated as an earlier preview and not stable.
For the latest behavior, use the current Firebase Hosting deployment and run the latest backend from this repository.

## Authorship Clarification

Project owner statement:

1. I am the person who came up with the core idea and the project structure.
2. I also proposed the endpoint-based game implementation concept.
3. Most coding was done using AI-assisted/vibe coding; I did not manually write most code myself.
4. I understand the system logic, including the PID-related parts.
5. For physics, I contributed the concept/idea direction.

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

## Disclaimer and License

1. Full legal disclaimer (English + Vietnamese): `DISCLAIMER.md`
2. License: `MIT` (see `LICENSE`)
