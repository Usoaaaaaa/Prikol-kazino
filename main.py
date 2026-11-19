import math
import random
import sys
import traceback
import pygame

RED_NUMS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
WHEEL_NUMS = (
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
    5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26,
)


class NeonCasino:
    def __init__(self):
        pygame.init()
        self.scr = pygame.display.set_mode((0, 0))
        self.w, self.h = self.scr.get_size()
        self.clock = pygame.time.Clock()

        self.f_xs = pygame.font.SysFont("sans", max(12, int(self.w * 0.026)), bold=True)
        self.f_sm = pygame.font.SysFont("sans", max(15, int(self.w * 0.035)), bold=True)
        self.f_md = pygame.font.SysFont("sans", max(20, int(self.w * 0.045)), bold=True)
        self.f_lg = pygame.font.SysFont("sans", max(28, int(self.w * 0.068)), bold=True)
        self.f_xl = pygame.font.SysFont("sans", max(40, int(self.w * 0.095)), bold=True)
        self.txt_cache = {}
        self.btn_cache = {}

        self.bal = 1000
        self.bet = 100
        self.tab = "bj"
        self.btns = []

        self.bj_p, self.bj_d, self.bj_act, self.bj_reveal = [], [], False, False
        self.bj_msg, self.bj_col = "Нажми «Раздать»", (255, 255, 255)
        self.bj_bg = None

        self.cr_act, self.cr_boom = False, False
        self.cr_mult, self.cr_target, self.cr_bet = 1.0, 1.0, 100
        self.cr_pts, self.cr_msg, self.cr_col = [], "Забери до взрыва!", (255, 255, 255)
        self.cr_bg = None

        self.rl_pick = "red"
        self.rl_ball_ang, self.rl_start_ang, self.rl_delta_ang = -90.0, -90.0, 0.0
        self.rl_t, self.rl_dur, self.rl_target, self.rl_bet = 0, 42, 0, 100
        self.rl_spinning, self.rl_has_res = False, False
        self.rl_msg, self.rl_col = "Выбери ставку и крути", (255, 255, 255)
        self.wheel_surf = self.make_wheel_surface()

        self.sl_syms = ("7", "GEM", "STAR", "CHERRY", "BAR")
        self.sl_reels = [[random.choice(self.sl_syms) for _ in range(4)] for _ in range(3)]
        self.sl_offs = [0.0, 0.0, 0.0]
        self.sl_spinning, self.sl_tick, self.sl_bet = False, 0, 100
        self.sl_finals = ("7", "GEM", "STAR")
        self.sl_msg, self.sl_col = "2 одинаковых = x3 | 3 = x5 | 777 = x15", (255, 255, 255)
        self.sym_surfs = {}
        self.sl_bg = None

    def get_txt(self, text, font, col):
        key = (text, id(font), col)
        surf = self.txt_cache.get(key)
        if surf is None:
            if len(self.txt_cache) > 120:
                self.txt_cache.clear()
            surf = font.render(text, True, col)
            self.txt_cache[key] = surf
        return surf

    def btn(self, rect, text, bg, fg=(255, 255, 255), border=None, action=None, font=None):
        r = pygame.Rect(rect)
        f = font or self.f_sm
        key = (r.width, r.height, text, bg, fg, border, id(f))
        surf = self.btn_cache.get(key)
        if surf is None:
            if len(self.btn_cache) > 80:
                self.btn_cache.clear()
            surf = pygame.Surface((r.width, r.height)).convert()
            surf.fill((1, 2, 3))
            surf.set_colorkey((1, 2, 3))
            pygame.draw.rect(surf, bg, (0, 0, r.width, r.height), border_radius=12)
            if border:
                pygame.draw.rect(surf, border, (0, 0, r.width, r.height), width=3, border_radius=12)
            lbl = self.get_txt(text, f, fg)
            surf.blit(lbl, lbl.get_rect(center=(r.width // 2, r.height // 2)))
            self.btn_cache[key] = surf
        self.scr.blit(surf, r.topleft)
        if action:
            self.btns.append((r, action))

    def take_bet(self):
        if self.bet <= 0 or self.bet > self.bal:
            return 0
        self.bal -= self.bet
        return self.bet

    def set_tab(self, t):
        if not self.cr_act and not self.rl_spinning and not self.sl_spinning:
            self.tab = t

    def change_bet(self, val):
        self.bet = max(10, min(max(10, self.bal), int(val)))

    def draw_hud(self):
        pad = 14
        top_h = int(self.h * 0.062)
        pygame.draw.rect(self.scr, (28, 22, 54), (0, 0, self.w, top_h))
        fps = int(self.clock.get_fps())
        b_lbl = self.get_txt(f"Баланс: {self.bal}$  ({fps} FPS)", self.f_sm, (255, 209, 102))
        self.scr.blit(b_lbl, (pad, (top_h - b_lbl.get_height()) // 2))

        xw = int(self.w * 0.11)
        aw = int(self.w * 0.22)
        self.btn((self.w - xw - 10, 6, xw, top_h - 12), "X", (230, 57, 70), action=sys.exit)
        self.btn((self.w - xw - aw - 16, 6, aw, top_h - 12), "+1000$", (6, 214, 160), (15, 12, 30), action=lambda: setattr(self, "bal", self.bal + 1000))

        y2 = top_h + 10
        bh = int(self.h * 0.048)
        cur_lbl = self.get_txt(f"Ставка: {self.bet}$", self.f_sm, (0, 245, 212))
        self.scr.blit(cur_lbl, (pad, y2 + (bh - cur_lbl.get_height()) // 2))

        adj = (("-50", lambda: self.change_bet(self.bet - 50)), ("+50", lambda: self.change_bet(self.bet + 50)), ("x2", lambda: self.change_bet(self.bet * 2)), ("MAX", lambda: self.change_bet(self.bal)))
        bw = int(self.w * 0.135)
        for i, (txt, fn) in enumerate(adj):
            self.btn((self.w - (4 - i) * (bw + 6) - 10, y2, bw, bh), txt, (46, 38, 82), action=fn)

        y3 = y2 + bh + 8
        pw = (self.w - 28 - 18) // 4
        for i, val in enumerate((50, 100, 250, 500)):
            sel = self.bet == val
            self.btn((14 + i * (pw + 6), y3, pw, bh), f"{val}$", (255, 209, 102) if sel else (38, 30, 70), (15, 12, 30) if sel else (255, 255, 255), action=lambda v=val: self.change_bet(v))

        y4 = y3 + bh + 10
        nh = int(self.h * 0.052)
        tw = (self.w - 28 - 18) // 4
        for i, (k, name) in enumerate((("bj", "Блэкджек"), ("crash", "Краш"), ("roul", "Рулетка"), ("slots", "Слоты"))):
            act = self.tab == k
            self.btn((14 + i * (tw + 6), y4, tw, nh), name, (255, 77, 109) if act else (38, 30, 70), action=lambda key=k: self.set_tab(key))

        return y4 + nh + 12
    def bj_val(self, hand):
        s = sum(11 if r == "A" else (10 if r in ("K", "Q", "J") else int(r)) for r, _, _ in hand)
        aces = sum(1 for r, _, _ in hand if r == "A")
        while s > 21 and aces:
            s -= 10
            aces -= 1
        return s

    def bj_new_card(self):
        ranks = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
        suits = ("S", "H", "D", "C")
        return [random.choice(ranks), random.choice(suits), 0.0]

    def bj_start(self):
        b = self.take_bet()
        if not b:
            return
        self.bj_bet, self.bj_act, self.bj_reveal = b, True, False
        self.bj_p = [self.bj_new_card(), self.bj_new_card()]
        self.bj_d = [self.bj_new_card(), self.bj_new_card()]
        self.bj_msg, self.bj_col = "Твой ход", (255, 255, 255)
        if self.bj_val(self.bj_p) == 21:
            self.bj_stand()

    def bj_hit(self):
        if not self.bj_act:
            return
        self.bj_p.append(self.bj_new_card())
        if self.bj_val(self.bj_p) > 21:
            self.bj_act, self.bj_reveal = False, True
            self.bj_msg, self.bj_col = "Перебор! Ты проиграл.", (255, 77, 109)

    def bj_stand(self):
        if not self.bj_act:
            return
        self.bj_act, self.bj_reveal = False, True
        while self.bj_val(self.bj_d) < 17:
            self.bj_d.append(self.bj_new_card())
        p, d = self.bj_val(self.bj_p), self.bj_val(self.bj_d)
        if d > 21 or p > d:
            win = self.bj_bet * 2
            self.bal += win
            self.bj_msg, self.bj_col = f"Победа! +{win}$", (6, 214, 160)
        elif p == d:
            self.bal += self.bj_bet
            self.bj_msg, self.bj_col = "Ничья! Возврат ставки.", (255, 209, 102)
        else:
            self.bj_msg, self.bj_col = "Дилер выиграл.", (255, 77, 109)

    def draw_suit(self, cx, cy, sz, suit, col):
        if suit == "D":
            pygame.draw.polygon(self.scr, col, ((cx, cy - sz), (cx + sz * 0.8, cy), (cx, cy + sz), (cx - sz * 0.8, cy)))
        elif suit == "H":
            r = int(sz * 0.45)
            pygame.draw.circle(self.scr, col, (int(cx - r * 0.9), int(cy - r * 0.4)), r)
            pygame.draw.circle(self.scr, col, (int(cx + r * 0.9), int(cy - r * 0.4)), r)
            pygame.draw.polygon(self.scr, col, ((cx - r * 1.85, cy - r * 0.2), (cx + r * 1.85, cy - r * 0.2), (cx, cy + sz)))
        elif suit == "S":
            r = int(sz * 0.42)
            pygame.draw.polygon(self.scr, col, ((cx, cy - sz), (cx + r * 1.85, cy + r * 0.35), (cx - r * 1.85, cy + r * 0.35)))
            pygame.draw.circle(self.scr, col, (int(cx - r * 0.9), int(cy + r * 0.45)), r)
            pygame.draw.circle(self.scr, col, (int(cx + r * 0.9), int(cy + r * 0.45)), r)
            pygame.draw.polygon(self.scr, col, ((cx, cy + r * 0.4), (cx + r * 0.8, cy + sz), (cx - r * 0.8, cy + sz)))
        else:
            r = int(sz * 0.40)
            pygame.draw.circle(self.scr, col, (int(cx), int(cy - sz * 0.45)), r)
            pygame.draw.circle(self.scr, col, (int(cx - r * 0.95), int(cy + r * 0.35)), r)
            pygame.draw.circle(self.scr, col, (int(cx + r * 0.95), int(cy + r * 0.35)), r)
            pygame.draw.polygon(self.scr, col, ((cx, cy + r * 0.2), (cx + r * 0.8, cy + sz), (cx - r * 0.8, cy + sz)))

    def draw_bj(self, top_y):
        msg = self.get_txt(self.bj_msg, self.f_md, self.bj_col)
        self.scr.blit(msg, msg.get_rect(center=(self.w // 2, top_y + 18)))

        table = pygame.Rect(14, top_y + 42, self.w - 28, int(self.h * 0.50))
        if self.bj_bg is None:
            self.bj_bg = pygame.Surface((table.width, table.height)).convert()
            self.bj_bg.fill((18, 14, 34))
            pygame.draw.rect(self.bj_bg, (20, 74, 52), (0, 0, table.width, table.height), border_radius=18)
            pygame.draw.rect(self.bj_bg, (255, 209, 102), (0, 0, table.width, table.height), width=3, border_radius=18)
        self.scr.blit(self.bj_bg, table.topleft)

        cw = min(int((table.width - 54) / 5), int(table.height * 0.26))
        ch = int(cw * 1.45)
        d_sc = self.bj_val(self.bj_d) if self.bj_reveal else "?"
        self.scr.blit(self.get_txt(f"Дилер: {d_sc}", self.f_sm, (255, 209, 102)), (table.x + 18, table.y + 12))
        self.scr.blit(self.get_txt(f"Ты: {self.bj_val(self.bj_p)}", self.f_sm, (0, 245, 212)), (table.x + 18, table.centery + 10))

        for row_idx, (hand, base_y) in enumerate(((self.bj_d, table.y + 44), (self.bj_p, table.centery + 42))):
            for i, card in enumerate(hand):
                rank, suit, prog = card
                if prog < 1.0:
                    prog = min(1.0, prog + 0.25)
                    card.clear()
                    card.extend((rank, suit, prog))
                tx = table.x + 18 + i * (cw + 8)
                cx = self.w + (tx - self.w) * (1 - (1 - prog) ** 3)
                rc = pygame.Rect(int(cx), int(base_y), cw, ch)
                if row_idx == 0 and i == 1 and not self.bj_reveal:
                    pygame.draw.rect(self.scr, (158, 25, 70), rc, border_radius=10)
                    pygame.draw.rect(self.scr, (255, 209, 102), rc.inflate(-10, -10), width=2, border_radius=6)
                else:
                    pygame.draw.rect(self.scr, (250, 250, 250), rc, border_radius=10)
                    col = (217, 4, 41) if suit in ("H", "D") else (20, 16, 36)
                    self.scr.blit(self.get_txt(rank, self.f_sm, col), (rc.x + 8, rc.y + 6))
                    self.draw_suit(rc.centerx, rc.centery + 10, min(cw, ch) * 0.23, suit, col)

        by = table.bottom + 14
        bw = (self.w - 28 - 16) // 3
        bh = int(self.h * 0.065)
        self.btn((14, by, bw, bh), "Раздать", (6, 214, 160), (15, 12, 30), action=self.bj_start, font=self.f_md)
        self.btn((14 + bw + 8, by, bw, bh), "Ещё", (255, 209, 102), (15, 12, 30), action=self.bj_hit, font=self.f_md)
        self.btn((14 + (bw + 8) * 2, by, bw, bh), "Хватит", (255, 77, 109), action=self.bj_stand, font=self.f_md)
    def cr_click(self):
        if not self.cr_act:
            b = self.take_bet()
            if not b:
                return
            self.cr_bet, self.cr_mult, self.cr_act, self.cr_boom = b, 1.0, True, False
            self.cr_pts = []
            self.cr_target = round(min(50.0, 0.96 / max(0.01, random.random())), 2)
            self.cr_msg, self.cr_col = "Ракета набирает высоту...", (0, 245, 212)
        else:
            self.cr_act = False
            win = int(self.cr_bet * self.cr_mult)
            self.bal += win
            self.cr_msg, self.cr_col = f"Успел! +{win}$ ({self.cr_mult:.2f}x)", (6, 214, 160)

    def draw_crash(self, top_y):
        box = pygame.Rect(14, top_y + 10, self.w - 28, int(self.h * 0.50))
        if self.cr_bg is None:
            self.cr_bg = pygame.Surface((box.width, box.height)).convert()
            self.cr_bg.fill((18, 14, 34))
            pygame.draw.rect(self.cr_bg, (14, 11, 28), (0, 0, box.width, box.height), border_radius=18)
            pygame.draw.rect(self.cr_bg, (57, 48, 83), (0, 0, box.width, box.height), width=3, border_radius=18)
            for i in range(1, 5):
                pygame.draw.line(self.cr_bg, (26, 21, 48), (0, box.height * i // 5), (box.width, box.height * i // 5))
                pygame.draw.line(self.cr_bg, (26, 21, 48), (box.width * i // 5, 0), (box.width * i // 5, box.height))
        self.scr.blit(self.cr_bg, box.topleft)

        rx, ry = box.x + 36, box.bottom - 36
        if self.cr_act:
            self.cr_mult = round(self.cr_mult + 0.03 + self.cr_mult * 0.014, 2)
            prog = min(1.0, (self.cr_mult - 1.0) / 5.5)
            rx = int(box.x + 36 + prog * (box.width - 80))
            ry = int(box.bottom - 36 - (prog ** 0.85) * (box.height - 85))
            self.cr_pts.append((rx, ry))
            if len(self.cr_pts) > 50:
                self.cr_pts.pop(0)
            if self.cr_mult >= self.cr_target:
                self.cr_act, self.cr_boom = False, True
                self.cr_msg, self.cr_col = f"Бум на {self.cr_target:.2f}x! Ставка сгорела.", (255, 77, 109)
        elif self.cr_pts:
            rx, ry = self.cr_pts[-1]

        if len(self.cr_pts) >= 2:
            pygame.draw.lines(self.scr, (255, 77, 109) if self.cr_boom else (0, 245, 212), False, self.cr_pts, 6)

        if self.cr_boom:
            pygame.draw.circle(self.scr, (255, 77, 109), (rx, ry), 20)
            pygame.draw.circle(self.scr, (255, 209, 102), (rx, ry), 10)
        else:
            pygame.draw.polygon(self.scr, (255, 209, 102), ((rx + 22, ry - 10), (rx - 12, ry - 15), (rx - 4, ry), (rx - 15, ry + 12)))
            pygame.draw.circle(self.scr, (255, 77, 109), (rx - 14, ry + 4), 6)

        val_show = self.cr_target if self.cr_boom else self.cr_mult
        m_lbl = self.get_txt(f"{val_show:.2f}x", self.f_xl, (255, 77, 109) if self.cr_boom else (0, 245, 212))
        self.scr.blit(m_lbl, m_lbl.get_rect(center=(box.centerx, box.y + int(box.height * 0.24))))

        st_lbl = self.get_txt(self.cr_msg, self.f_md, self.cr_col)
        self.scr.blit(st_lbl, st_lbl.get_rect(center=(self.w // 2, box.bottom + 26)))

        btn_txt = "Забрать!" if self.cr_act else "Старт"
        btn_col = (255, 209, 102) if self.cr_act else (6, 214, 160)
        self.btn((24, box.bottom + 54, self.w - 48, int(self.h * 0.068)), btn_txt, btn_col, (15, 12, 30), action=self.cr_click, font=self.f_lg)

    def make_wheel_surface(self):
        rad = int(min(self.w * 0.34, self.h * 0.165))
        sz = rad * 2 + 24
        surf = pygame.Surface((sz, sz)).convert()
        surf.fill((18, 14, 34))
        cx = cy = sz // 2
        pygame.draw.circle(surf, (92, 61, 46), (cx, cy), rad + 9)
        pygame.draw.circle(surf, (255, 209, 102), (cx, cy), rad + 9, 3)
        step = 360.0 / 37.0
        for i, num in enumerate(WHEEL_NUMS):
            a1 = math.radians(-90 - (i + 0.5) * step)
            a2 = math.radians(-90 - (i - 0.5) * step)
            col = (6, 214, 160) if num == 0 else ((230, 57, 70) if num in RED_NUMS else (24, 22, 42))
            pts = [(cx, cy)]
            for k in range(4):
                a = a1 + (a2 - a1) * (k / 3.0)
                pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, (255, 209, 102), pts, 1)
            mid = math.radians(-90 - i * step)
            tx = cx + rad * 0.82 * math.cos(mid)
            ty = cy + rad * 0.82 * math.sin(mid)
            t_img = self.f_xs.render(str(num), True, (255, 255, 255))
            surf.blit(t_img, t_img.get_rect(center=(tx, ty)))
        pygame.draw.circle(surf, (28, 22, 54), (cx, cy), int(rad * 0.58))
        pygame.draw.circle(surf, (255, 209, 102), (cx, cy), int(rad * 0.58), 2)
        return surf
    def rl_check(self, num, pick):
        if pick == "green":
            return num == 0
        if num == 0:
            return False
        if pick == "red":
            return num in RED_NUMS
        if pick == "black":
            return num not in RED_NUMS
        if pick == "even":
            return num % 2 == 0
        if pick == "odd":
            return num % 2 == 1
        if pick == "low":
            return 1 <= num <= 18
        return 19 <= num <= 36

    def rl_spin(self):
        if self.rl_spinning:
            return
        b = self.take_bet()
        if not b:
            return
        self.rl_bet, self.rl_spinning, self.rl_t, self.rl_has_res = b, True, 0, False
        self.rl_target = random.choice(WHEEL_NUMS)
        idx = WHEEL_NUMS.index(self.rl_target)
        step = 360.0 / 37.0
        target_ang = (-90.0 - idx * step) % 360.0
        cur_ang = self.rl_ball_ang % 360.0
        self.rl_start_ang = self.rl_ball_ang
        self.rl_delta_ang = (target_ang - cur_ang) % 360.0 + 360.0 * 4
        self.rl_msg, self.rl_col = "Шарик катится...", (255, 209, 102)

    def draw_roul(self, top_y):
        prog = 1.0
        if self.rl_spinning:
            self.rl_t += 1
            prog = min(1.0, self.rl_t / self.rl_dur)
            eased = 1 - (1 - prog) ** 3
            self.rl_ball_ang = self.rl_start_ang + self.rl_delta_ang * eased
            if self.rl_t >= self.rl_dur:
                self.rl_spinning, self.rl_has_res = False, True
                if self.rl_check(self.rl_target, self.rl_pick):
                    mult = 14 if self.rl_pick == "green" else 2
                    win = self.rl_bet * mult
                    self.bal += win
                    self.rl_msg, self.rl_col = f"Выпало {self.rl_target}! Выигрыш +{win}$", (6, 214, 160)
                else:
                    self.rl_msg, self.rl_col = f"Выпало {self.rl_target}. Мимо!", (255, 77, 109)

        cx = self.w // 2
        wh = self.wheel_surf.get_height()
        cy = top_y + wh // 2 + 6
        self.scr.blit(self.wheel_surf, self.wheel_surf.get_rect(center=(cx, cy)))

        rad = (wh - 24) // 2
        orbit = rad * (0.94 - 0.26 * (prog ** 2))
        brad = math.radians(self.rl_ball_ang)
        bx = int(cx + orbit * math.cos(brad))
        by_ball = int(cy + orbit * math.sin(brad))
        pygame.draw.circle(self.scr, (255, 255, 255), (bx, by_ball), 9)
        pygame.draw.circle(self.scr, (20, 16, 36), (bx, by_ball), 9, 2)

        if self.rl_has_res:
            res_t = self.get_txt(str(self.rl_target), self.f_lg, (255, 209, 102))
            self.scr.blit(res_t, res_t.get_rect(center=(cx, cy)))

        names = {"red": "КРАСНОЕ (x2)", "green": "ЗЕРО 0 (x14)", "black": "ЧЁРНОЕ (x2)", "even": "ЧЁТНОЕ (x2)", "odd": "НЕЧЁТНОЕ (x2)", "low": "1 - 18 (x2)", "high": "19 - 36 (x2)"}
        y_info = cy + wh // 2 + 14
        p_t = self.get_txt(f"Ставка на: {names[self.rl_pick]}", self.f_sm, (255, 209, 102))
        self.scr.blit(p_t, p_t.get_rect(center=(cx, y_info)))
        m_t = self.get_txt(self.rl_msg, self.f_md, self.rl_col)
        self.scr.blit(m_t, m_t.get_rect(center=(cx, y_info + 28)))

        rows = (
            (("red", "Красное x2", (230, 57, 70)), ("green", "Зеро x14", (6, 214, 160)), ("black", "Чёрное x2", (30, 28, 48))),
            (("even", "Чёт x2", (46, 38, 82)), ("odd", "Нечёт x2", (46, 38, 82))),
            (("low", "1-18 x2", (46, 38, 82)), ("high", "19-36 x2", (46, 38, 82))),
        )
        by = y_info + 52
        bh = int(self.h * 0.048)
        for r_opts in rows:
            bw = (self.w - 28 - (len(r_opts) - 1) * 6) // len(r_opts)
            for i, (k, txt, col) in enumerate(r_opts):
                brd = (255, 209, 102) if self.rl_pick == k else None
                self.btn((14 + i * (bw + 6), by, bw, bh), txt, col, (15, 12, 30) if k == "green" else (255, 255, 255), brd, action=lambda key=k: setattr(self, "rl_pick", key))
            by += bh + 6

        self.btn((20, by + 6, self.w - 40, int(self.h * 0.062)), "Крутить рулетку", (255, 209, 102), (15, 12, 30), action=self.rl_spin, font=self.f_md)
    def get_sym_surf(self, sym, sz):
        key = (sym, int(sz))
        if key in self.sym_surfs:
            return self.sym_surfs[key]
        side = int(sz * 2.4)
        s = pygame.Surface((side, side)).convert()
        s.fill((26, 20, 48))
        cx = cy = side // 2
        if sym == "7":
            t = self.f_xl.render("7", True, (255, 209, 102))
            s.blit(t, t.get_rect(center=(cx, cy)))
        elif sym == "GEM":
            pygame.draw.polygon(s, (0, 245, 212), ((cx, cy - sz), (cx + sz * 0.85, cy), (cx, cy + sz), (cx - sz * 0.85, cy)))
        elif sym == "STAR":
            pts = []
            for i in range(10):
                ang = math.radians(-90 + i * 36)
                r = sz if i % 2 == 0 else sz * 0.42
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
            pygame.draw.polygon(s, (255, 159, 28), pts)
        elif sym == "CHERRY":
            r = int(sz * 0.36)
            pygame.draw.line(s, (6, 214, 160), (cx - r, cy + r * 0.3), (cx, cy - sz * 0.85), 3)
            pygame.draw.line(s, (6, 214, 160), (cx + r, cy + r * 0.3), (cx, cy - sz * 0.85), 3)
            pygame.draw.circle(s, (255, 77, 109), (int(cx - r), int(cy + r * 0.7)), r)
            pygame.draw.circle(s, (255, 77, 109), (int(cx + r), int(cy + r * 0.7)), r)
        else:
            r_bar = pygame.Rect(int(cx - sz * 1.1), int(cy - sz * 0.52), int(sz * 2.2), int(sz * 1.04))
            pygame.draw.rect(s, (6, 214, 160), r_bar, border_radius=8)
            t = self.f_md.render("BAR", True, (15, 12, 30))
            s.blit(t, t.get_rect(center=r_bar.center))
        self.sym_surfs[key] = s
        return s

    def sl_spin(self):
        if self.sl_spinning:
            return
        b = self.take_bet()
        if not b:
            return
        self.sl_bet, self.sl_spinning, self.sl_tick = b, True, 0
        self.sl_finals = (random.choice(self.sl_syms), random.choice(self.sl_syms), random.choice(self.sl_syms))
        self.sl_msg, self.sl_col = "Барабаны крутятся...", (255, 209, 102)

    def draw_slots(self, top_y):
        box = pygame.Rect(14, top_y + 12, self.w - 28, int(self.h * 0.44))
        cell_h = box.height / 3.0
        rw = (box.width - 36) / 3.0
        sz = min(rw, cell_h) * 0.28

        if self.sl_bg is None:
            self.sl_bg = pygame.Surface((box.width, box.height)).convert()
            self.sl_bg.fill((18, 14, 34))
            pygame.draw.rect(self.sl_bg, (14, 11, 28), (0, 0, box.width, box.height), border_radius=18)
            for i in range(3):
                rx = 9 + i * (rw + 9)
                pygame.draw.rect(self.sl_bg, (26, 20, 48), (rx, 6, rw, box.height - 12), border_radius=12)

        self.scr.blit(self.sl_bg, box.topleft)

        if self.sl_spinning:
            self.sl_tick += 1
            stops = (18, 26, 34)
            new_offs = []
            for reel, off, fs, st in zip(self.sl_reels, self.sl_offs, self.sl_finals, stops):
                if self.sl_tick < st:
                    off += cell_h * (0.68 if self.sl_tick < st - 5 else 0.36)
                    while off >= cell_h:
                        off -= cell_h
                        reel.pop()
                        nxt = fs if self.sl_tick >= st - 3 else random.choice(self.sl_syms)
                        reel.insert(0, nxt)
                    new_offs.append(off)
                else:
                    s_top, s_mid, s_bot, s_ex = reel
                    reel.clear()
                    reel.extend((s_top, fs, s_bot, s_ex))
                    new_offs.append(0.0)
            self.sl_offs = new_offs

            if self.sl_tick >= 34:
                self.sl_spinning = False
                f0, f1, f2 = self.sl_finals
                if f0 == f1 == f2:
                    is_jp = f0 == "7"
                    mult = 15 if is_jp else 5
                    win = self.sl_bet * mult
                    self.bal += win
                    title = "ДЖЕКПОТ!" if is_jp else "Победа!"
                    self.sl_col = (255, 209, 102) if is_jp else (6, 214, 160)
                    self.sl_msg = f"{title} +{win}$ (x{mult})"
                elif f0 == f1 or f1 == f2 or f0 == f2:
                    win = self.sl_bet * 3
                    self.bal += win
                    self.sl_msg, self.sl_col = f"Победа! +{win}$ (x3)", (6, 214, 160)
                else:
                    self.sl_msg, self.sl_col = "Не совпало, крути ещё!", (255, 77, 109)

        clip_r = pygame.Rect(box.x + 6, box.y + 8, box.width - 12, box.height - 16)
        self.scr.set_clip(clip_r)
        for i, (reel, off) in enumerate(zip(self.sl_reels, self.sl_offs)):
            cx = box.x + 9 + i * (rw + 9) + rw / 2
            s_top, s_mid, s_bot, s_ex = reel
            for r_i, sym in ((-1, s_ex), (0, s_top), (1, s_mid), (2, s_bot)):
                cy = box.y + (r_i + 0.5) * cell_h + off
                img = self.get_sym_surf(sym, sz)
                self.scr.blit(img, img.get_rect(center=(cx, cy)))
        self.scr.set_clip(None)

        pygame.draw.rect(self.scr, (255, 209, 102), (box.x + 4, int(box.y + cell_h), box.width - 8, int(cell_h)), width=4, border_radius=12)
        m_lbl = self.get_txt(self.sl_msg, self.f_md, self.sl_col)
        self.scr.blit(m_lbl, m_lbl.get_rect(center=(self.w // 2, box.bottom + 26)))
        self.btn((24, box.bottom + 54, self.w - 48, int(self.h * 0.068)), "Крутить слоты!", (155, 93, 229), action=self.sl_spin, font=self.f_lg)

    def run(self):
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    sys.exit()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    for rect, fn in list(self.btns):
                        if rect.collidepoint(ev.pos):
                            fn()

            self.btns.clear()
            self.scr.fill((18, 14, 34))
            top_y = self.draw_hud()
            getattr(self, f"draw_{self.tab}")(top_y)
            pygame.display.flip()
            self.clock.tick(30)


if __name__ == "__main__":
    try:
        NeonCasino().run()
    except Exception:
        err = traceback.format_exc()
        print(err)
        pygame.quit()
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка", err)
