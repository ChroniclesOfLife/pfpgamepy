"""Single-view UI for race, betting, chat, notifications, and education overlay."""

from __future__ import annotations

import pygame

from shared import constants


class UIManager:
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Consolas", 26, bold=True)
        self.font_med = pygame.font.SysFont("Consolas", 18)
        self.font_small = pygame.font.SysFont("Consolas", 14)

        self.name_text = "Player"
        self.room_text = "Lobby1"

        self.chat_input = ""
        self.focus_chat = False

        self.selected_car = "car1"
        self.selected_amount = 50
        self.amount_options = [25, 50, 100, 250]
        self.coupon_codes = ["BOOST100", "LUCK250", "RISKY-120"]

        self.warn_x = 90.0
        self.warn_y = 90.0
        self.warn_vx = 2.8
        self.warn_vy = 2.1

    def _button(self, x, y, w, h):
        return pygame.Rect(x, y, w, h)

    def step_warning(self):
        self.warn_x += self.warn_vx
        self.warn_y += self.warn_vy
        bw, bh = 420, 34
        if self.warn_x < 0 or self.warn_x + bw > constants.WIDTH:
            self.warn_vx *= -1
        if self.warn_y < 0 or self.warn_y + bh > constants.HEIGHT:
            self.warn_vy *= -1
        self.warn_x = max(0, min(constants.WIDTH - bw, self.warn_x))
        self.warn_y = max(0, min(constants.HEIGHT - bh, self.warn_y))

    def handle_event(self, event):
        actions = []

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            join_rect = self._button(constants.SIDEBAR_X + 18, 18, 170, 32)
            if join_rect.collidepoint(mx, my):
                actions.append({"type": "join"})

            for i in range(5):
                car_rect = self._button(constants.SIDEBAR_X + 18, 92 + i * 28, 84, 22)
                if car_rect.collidepoint(mx, my):
                    self.selected_car = f"car{i+1}"
                    actions.append({"type": "select_car", "car_id": self.selected_car})

            for idx, amt in enumerate(self.amount_options):
                r = self._button(constants.SIDEBAR_X + 112 + idx * 58, 92, 54, 22)
                if r.collidepoint(mx, my):
                    self.selected_amount = amt

            place_rect = self._button(constants.SIDEBAR_X + 18, 248, 170, 30)
            if place_rect.collidepoint(mx, my):
                actions.append({"type": "bet", "car_id": self.selected_car, "amount": self.selected_amount})

            for idx, code in enumerate(self.coupon_codes):
                c_rect = self._button(constants.SIDEBAR_X + 18 + idx * 116, 286, 108, 24)
                if c_rect.collidepoint(mx, my):
                    actions.append({"type": "coupon", "code": code})

            chat_box = self._button(constants.SIDEBAR_X + 18, 626, 390, 28)
            self.focus_chat = chat_box.collidepoint(mx, my)

            send_rect = self._button(constants.SIDEBAR_X + 312, 660, 96, 26)
            if send_rect.collidepoint(mx, my):
                actions.append({"type": "chat_send", "text": self.chat_input.strip()})
                self.chat_input = ""

            ai_rect = self._button(constants.SIDEBAR_X + 206, 660, 98, 26)
            if ai_rect.collidepoint(mx, my):
                actions.append({"type": "chat_send", "text": "/ai exacta + longshot update"})

        if event.type == pygame.KEYDOWN and self.focus_chat:
            if event.key == pygame.K_RETURN:
                actions.append({"type": "chat_send", "text": self.chat_input.strip()})
                self.chat_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.chat_input = self.chat_input[:-1]
            else:
                if event.unicode and event.unicode.isprintable() and len(self.chat_input) < 120:
                    self.chat_input += event.unicode

        return actions

    def draw(self, screen, state, chat_events, leaderboard, sentiment_text, notifications, wallet, connected_uri):
        screen.fill(constants.BLACK)

        race_rect = pygame.Rect(0, 0, constants.RACE_PANEL_W, constants.HEIGHT)
        pygame.draw.rect(screen, constants.TRACK_BG, race_rect)

        outer = pygame.Rect(constants.TRACK_OUTER_X, constants.TRACK_OUTER_Y, constants.TRACK_OUTER_W, constants.TRACK_OUTER_H)
        inner = pygame.Rect(constants.TRACK_INNER_X, constants.TRACK_INNER_Y, constants.TRACK_INNER_W, constants.TRACK_INNER_H)
        pygame.draw.rect(screen, constants.NEON_CYAN, outer, width=3)
        pygame.draw.rect(screen, constants.NEON_PINK, inner, width=3)

        for lane in range(constants.LANE_COUNT):
            inset = 20 + lane * 16
            lane_rect = pygame.Rect(
                constants.TRACK_OUTER_X + inset,
                constants.TRACK_OUTER_Y + inset,
                constants.TRACK_OUTER_W - inset * 2,
                constants.TRACK_OUTER_H - inset * 2,
            )
            pygame.draw.rect(screen, (45, 52, 70), lane_rect, width=1)

        cars = state.get("cars", []) if state else []
        for c in cars:
            color = tuple(c.get("color", [255, 255, 255]))
            r = pygame.Rect(int(c.get("x", 0)), int(c.get("y", 0)), constants.CAR_WIDTH, constants.CAR_HEIGHT)
            pygame.draw.rect(screen, color, r, border_radius=4)
            tag = self.font_small.render(c.get("name", "CAR"), True, constants.WHITE)
            screen.blit(tag, (r.x, r.y - 14))

        sidebar = pygame.Rect(constants.SIDEBAR_X, 0, constants.WIDTH - constants.SIDEBAR_X, constants.HEIGHT)
        pygame.draw.rect(screen, constants.PANEL_BG, sidebar)

        title = self.font_title.render("Race + Wagers + AI Chat", True, constants.WHITE)
        screen.blit(title, (constants.SIDEBAR_X + 14, 18))

        join_rect = self._button(constants.SIDEBAR_X + 210, 18, 198, 32)
        pygame.draw.rect(screen, (32, 92, 62), join_rect, border_radius=6)
        screen.blit(self.font_small.render("Connect / Join Room", True, constants.WHITE), (join_rect.x + 18, join_rect.y + 8))

        phase = state.get("phase", "-") if state else "-"
        race_no = state.get("race_no", 0) if state else 0
        screen.blit(self.font_small.render(f"Room: {self.room_text} | Player: {self.name_text}", True, constants.WHITE), (constants.SIDEBAR_X + 18, 58))
        screen.blit(self.font_small.render(f"Race #{race_no} | Phase: {phase}", True, constants.YELLOW), (constants.SIDEBAR_X + 18, 76))
        if connected_uri:
            screen.blit(self.font_small.render(f"Endpoint: {connected_uri}", True, constants.NEON_GREEN), (constants.SIDEBAR_X + 18, 332))

        screen.blit(self.font_med.render("Quick Bet (1-2 taps)", True, constants.GOLD), (constants.SIDEBAR_X + 18, 92))
        for i in range(5):
            cid = f"car{i+1}"
            sel = cid == self.selected_car
            car_rect = self._button(constants.SIDEBAR_X + 18, 116 + i * 26, 84, 22)
            pygame.draw.rect(screen, (90, 140, 210) if sel else (52, 64, 86), car_rect, border_radius=5)
            screen.blit(self.font_small.render(cid.upper(), True, constants.WHITE), (car_rect.x + 10, car_rect.y + 4))

        for idx, amt in enumerate(self.amount_options):
            sel = amt == self.selected_amount
            r = self._button(constants.SIDEBAR_X + 112 + idx * 58, 116, 54, 22)
            pygame.draw.rect(screen, (74, 160, 88) if sel else (52, 64, 86), r, border_radius=5)
            screen.blit(self.font_small.render(f"${amt}", True, constants.WHITE), (r.x + 10, r.y + 4))

        place_rect = self._button(constants.SIDEBAR_X + 18, 248, 170, 30)
        pygame.draw.rect(screen, (175, 78, 48), place_rect, border_radius=6)
        screen.blit(self.font_small.render("PLACE BET", True, constants.WHITE), (place_rect.x + 48, place_rect.y + 9))

        screen.blit(self.font_small.render("Coupons", True, constants.GOLD), (constants.SIDEBAR_X + 18, 286))
        for idx, code in enumerate(self.coupon_codes):
            c_rect = self._button(constants.SIDEBAR_X + 18 + idx * 116, 308, 108, 24)
            pygame.draw.rect(screen, (56, 78, 112), c_rect, border_radius=5)
            screen.blit(self.font_small.render(code, True, constants.WHITE), (c_rect.x + 10, c_rect.y + 5))

        if wallet:
            screen.blit(self.font_small.render(f"Money: ${wallet.get('money', 0)}", True, constants.NEON_GREEN), (constants.SIDEBAR_X + 18, 356))
            screen.blit(self.font_small.render(f"Wins: {wallet.get('wins', 0)}", True, constants.WHITE), (constants.SIDEBAR_X + 150, 356))
            badges = ", ".join(wallet.get("badges", [])) or "No badges yet"
            screen.blit(self.font_small.render(f"Badges: {badges}", True, constants.WHITE), (constants.SIDEBAR_X + 18, 374))

        screen.blit(self.font_small.render("Rankings", True, constants.GOLD), (constants.SIDEBAR_X + 18, 402))
        for idx, entry in enumerate(state.get("rankings", [])[:5] if state else []):
            txt = f"{entry['place']}. {entry['name']} L{entry['lap']} O:{entry['odds']:.2f}"
            screen.blit(self.font_small.render(txt, True, constants.WHITE), (constants.SIDEBAR_X + 18, 424 + idx * 18))

        screen.blit(self.font_small.render("Leaderboard", True, constants.GOLD), (constants.SIDEBAR_X + 18, 520))
        for idx, row in enumerate(leaderboard[:5]):
            txt = f"{idx+1}. {row['name']} ${row['score']}"
            screen.blit(self.font_small.render(txt, True, constants.WHITE), (constants.SIDEBAR_X + 18, 542 + idx * 16))

        chat_panel = pygame.Rect(constants.SIDEBAR_X + 18, 596, 390, 118)
        pygame.draw.rect(screen, (21, 27, 41), chat_panel, border_radius=6)
        screen.blit(self.font_small.render("Chat + WagersBot", True, constants.GOLD), (chat_panel.x + 8, chat_panel.y + 6))

        latest = chat_events[-4:]
        for i, ev in enumerate(latest):
            prefix = "AI" if ev.get("kind") == "ai" else ev.get("sender", "P")
            msg = f"{prefix}: {ev.get('message', '')}"
            color = constants.NEON_CYAN if ev.get("kind") == "ai" else constants.WHITE
            screen.blit(self.font_small.render(msg[:58], True, color), (chat_panel.x + 8, chat_panel.y + 26 + i * 16))

        chat_box = self._button(constants.SIDEBAR_X + 18, 626, 390, 28)
        pygame.draw.rect(screen, (31, 38, 56), chat_box, border_radius=5)
        screen.blit(self.font_small.render(self.chat_input or "Type message or /ai exacta", True, constants.WHITE), (chat_box.x + 8, chat_box.y + 7))

        ai_rect = self._button(constants.SIDEBAR_X + 206, 660, 98, 26)
        send_rect = self._button(constants.SIDEBAR_X + 312, 660, 96, 26)
        pygame.draw.rect(screen, (44, 90, 124), ai_rect, border_radius=5)
        pygame.draw.rect(screen, (58, 116, 70), send_rect, border_radius=5)
        screen.blit(self.font_small.render("Ask AI", True, constants.WHITE), (ai_rect.x + 24, ai_rect.y + 6))
        screen.blit(self.font_small.render("Send", True, constants.WHITE), (send_rect.x + 30, send_rect.y + 6))

        if sentiment_text:
            s = self.font_small.render(f"Sentiment: {sentiment_text}", True, constants.YELLOW)
            screen.blit(s, (constants.SIDEBAR_X + 18, 690))

        notes = notifications[-2:]
        for i, note in enumerate(notes):
            txt = note.get("text", "")
            col = constants.NEON_PINK if note.get("kind") in {"alert", "flag"} else constants.WHITE
            screen.blit(self.font_small.render(txt[:60], True, col), (constants.SIDEBAR_X + 18, 710 + i * 16))

        self.step_warning()
        warning = pygame.Surface((420, 34), pygame.SRCALPHA)
        warning.fill((255, 180, 60, 65))
        warning_txt = self.font_small.render("EDUCATION PURPOSES ONLY: simulated racing + wager mechanics.", True, (255, 255, 255))
        warning.blit(warning_txt, (10, 9))
        screen.blit(warning, (int(self.warn_x), int(self.warn_y)))
