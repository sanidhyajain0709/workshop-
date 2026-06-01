"""
👃 NOSE DODGE GAME 👃
Control your character using your NOSE via webcam!
Dodge falling poop emojis/obstacles to survive!

Requirements:
    pip install opencv-python numpy

Optional (better nose tracking):
    pip install mediapipe
"""

import cv2
import numpy as np
import random
import time

# ─── Try mediapipe ────────────────────────────────────────────────────────────
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

# ─── Constants ────────────────────────────────────────────────────────────────
GAME_W, GAME_H = 800, 600

COLORS = {
    "bg":      (30,  10,  15),
    "text":    (255, 255, 255),
    "gold":    (30,  215, 255),
    "hud_bg":  (40,  30,  60),
    "green":   (80,  200, 120),
}

OBSTACLES = [
    {"label": "POOP",  "color": (30,  100, 160), "speed_mult": 1.0, "size": 28, "pts": -10},
    {"label": "BOMB",  "color": (60,  60,  200), "speed_mult": 1.5, "size": 24, "pts": -20},
    {"label": "VIRUS", "color": (60,  180,  60), "speed_mult": 0.8, "size": 34, "pts": -15},
]

POWERUPS = [
    {"label": "STAR",  "color": (20,  200, 240), "size": 22, "effect": "shield", "pts": 50},
    {"label": "HEART", "color": (80,   60, 220), "size": 22, "effect": "life",   "pts": 30},
]


# ─── Helpers ──────────────────────────────────────────────────────────────────
def draw_text(img, text, pos, scale=1.0, color=(255, 255, 255),
              thickness=2, font=cv2.FONT_HERSHEY_DUPLEX, shadow=True):
    x, y = int(pos[0]), int(pos[1])
    if shadow:
        cv2.putText(img, text, (x + 2, y + 2), font, scale,
                    (0, 0, 0), thickness + 1, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), font, scale,
                tuple(int(c) for c in color), thickness, cv2.LINE_AA)


def draw_symbol(img, label, cx, cy, size, color):
    cx, cy, size = int(cx), int(cy), int(size)
    color = tuple(int(c) for c in color)

    if label == "POOP":
        cv2.circle(img, (cx, cy + size // 4),  size // 2, (30,  60, 100), -1)
        cv2.circle(img, (cx, cy - size // 6),  size // 3, (40,  75, 120), -1)
        cv2.circle(img, (cx, cy - size // 2),  size // 4, (50,  90, 140), -1)
        cv2.circle(img, (cx - 6, cy + 2), 3, (255, 255, 255), -1)
        cv2.circle(img, (cx + 6, cy + 2), 3, (255, 255, 255), -1)
        cv2.circle(img, (cx - 5, cy + 3), 2, (0,   0,   0),   -1)
        cv2.circle(img, (cx + 7, cy + 3), 2, (0,   0,   0),   -1)

    elif label == "BOMB":
        cv2.circle(img, (cx, cy), size // 2, (30, 30, 40), -1)
        cv2.circle(img, (cx, cy), size // 2, (70, 70, 90),  2)
        cv2.line(img, (cx, cy - size // 2), (cx + 5, cy - size // 2 - 10), (80, 120, 220), 2)
        cv2.circle(img, (cx + 7, cy - size // 2 - 12), 4, (20, 200, 255), -1)

    elif label == "VIRUS":
        cv2.circle(img, (cx, cy), size // 2, color, -1)
        for angle in range(0, 360, 45):
            rad = np.radians(angle)
            ex = int(cx + (size // 2 + 8) * np.cos(rad))
            ey = int(cy + (size // 2 + 8) * np.sin(rad))
            bx = int(cx + (size // 2)     * np.cos(rad))
            by = int(cy + (size // 2)     * np.sin(rad))
            cv2.line(img, (bx, by), (ex, ey), color, 2)
            cv2.circle(img, (ex, ey), 4, (100, 220, 100), -1)
        cv2.circle(img, (cx - 5, cy - 4), 4, (255, 255, 255), -1)
        cv2.circle(img, (cx + 5, cy - 4), 4, (255, 255, 255), -1)

    elif label == "STAR":
        pts = []
        for i in range(5):
            o_a = np.radians(i * 72 - 90)
            i_a = np.radians(i * 72 - 90 + 36)
            pts.append([int(cx + size // 2 * np.cos(o_a)),
                        int(cy + size // 2 * np.sin(o_a))])
            pts.append([int(cx + size // 4 * np.cos(i_a)),
                        int(cy + size // 4 * np.sin(i_a))])
        cv2.fillPoly(img, [np.array(pts, dtype=np.int32)], (20, 200, 240))

    elif label == "HEART":
        cv2.circle(img, (cx - size // 4, cy - 2), size // 4, color, -1)
        cv2.circle(img, (cx + size // 4, cy - 2), size // 4, color, -1)
        pts = np.array([[cx - size // 2, cy],
                        [cx,             cy + size // 2 + 2],
                        [cx + size // 2, cy]], dtype=np.int32)
        cv2.fillPoly(img, [pts], color)

    elif label == "PLAYER":
        cv2.circle(img, (cx, cy), size, color, -1)
        cv2.circle(img, (cx - size // 3, cy - size // 4), size // 5, (255, 255, 255), -1)
        cv2.circle(img, (cx + size // 3, cy - size // 4), size // 5, (255, 255, 255), -1)
        cv2.circle(img, (cx - size // 3 + 2, cy - size // 4 + 2), size // 8, (0, 0, 0), -1)
        cv2.circle(img, (cx + size // 3 + 2, cy - size // 4 + 2), size // 8, (0, 0, 0), -1)
        cv2.ellipse(img, (cx, cy + size // 5), (size // 3, size // 5),
                    0, 0, 180, (0, 0, 0), 2)
        cv2.circle(img, (cx, cy), 5, (255, 200, 100), -1)


# ─── Particle ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -1)
        self.life = 1.0
        self.color = color
        self.size = random.randint(3, 8)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.2
        self.life -= 0.04
        return self.life > 0

    def draw(self, img):
        c = tuple(int(v * self.life) for v in self.color)
        cv2.circle(img, (int(self.x), int(self.y)), self.size, c, -1)


# ─── Game ─────────────────────────────────────────────────────────────────────
class NoseDodgeGame:
    def __init__(self):
        # ── Face tracker ────────────────────────────────────────────────────
        if MEDIAPIPE_AVAILABLE:
            self.mp_face   = mp.solutions.face_mesh
            self.face_mesh = self.mp_face.FaceMesh(
                max_num_faces=1, refine_landmarks=True,
                min_detection_confidence=0.5, min_tracking_confidence=0.5)
            self.tracking_mode = "mediapipe"
        else:
            cascade = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade  = cv2.CascadeClassifier(cascade)
            self.tracking_mode = "haar"

        self.nose_x   = GAME_W // 2
        self.nose_y   = GAME_H // 2
        self.smooth_x = GAME_W // 2
        self.smooth_y = GAME_H // 2

        # Pre-generate a fixed random starfield (plain Python ints → safe for OpenCV)
        self.stars = [(random.randint(0, GAME_W - 1),
                       random.randint(0, GAME_H - 1),
                       random.randint(40, 140)) for _ in range(80)]

        self.state = "intro"
        self.reset()

    def reset(self):
        self.score       = 0
        self.lives       = 3
        self.shield      = 0
        self.level       = 1
        self.obstacles   = []
        self.powerups    = []
        self.particles   = []
        self.spawn_timer = 0
        self.pu_timer    = 0
        self.level_timer = time.time()
        self.dodge_count = 0
        self.frame_count = 0

    # ── Nose detection ────────────────────────────────────────────────────────
    def get_nose(self, frame):
        h, w = frame.shape[:2]
        if self.tracking_mode == "mediapipe":
            rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb)
            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark
                return int(lm[1].x * w), int(lm[1].y * h)
        else:
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
            if len(faces):
                fx, fy, fw, fh = faces[0]
                return fx + fw // 2, fy + int(fh * 0.65)
        return None, None

    # ── Spawn ─────────────────────────────────────────────────────────────────
    def spawn_obstacle(self):
        o = dict(random.choice(OBSTACLES))
        o["x"]     = random.randint(40, GAME_W - 40)
        o["y"]     = -40
        o["speed"] = (2 + self.level * 0.5) * o["speed_mult"] + random.uniform(-0.5, 0.5)
        o["wob"]   = random.uniform(0, 6.28)
        o["wob_s"] = random.uniform(0.05, 0.15)
        o["wob_a"] = random.uniform(0, 25)
        self.obstacles.append(o)

    def spawn_powerup(self):
        p = dict(random.choice(POWERUPS))
        p["x"] = random.randint(40, GAME_W - 40)
        p["y"] = -30
        p["speed"] = 1.8
        self.powerups.append(p)

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self):
        if self.state != "playing":
            return

        self.frame_count += 1

        # Level up every 20 s
        if time.time() - self.level_timer > 20:
            self.level = min(self.level + 1, 8)
            self.level_timer = time.time()
            self.score += 100 * self.level

        # Smooth nose (lerp)
        S = 0.25
        self.smooth_x = int(self.smooth_x * (1 - S) + self.nose_x * S)
        self.smooth_y = int(self.smooth_y * (1 - S) + self.nose_y * S)
        px, py = self.smooth_x, self.smooth_y
        PR = 22   # player radius

        # Spawn timers
        self.spawn_timer += 1
        rate = max(12, 35 - self.level * 3)
        if self.spawn_timer >= rate:
            self.spawn_timer = 0
            for _ in range(1 + self.level // 4):
                self.spawn_obstacle()

        self.pu_timer += 1
        if self.pu_timer >= 180:
            self.pu_timer = 0
            self.spawn_powerup()

        if self.shield > 0:
            self.shield -= 1

        # Obstacles
        alive = []
        for o in self.obstacles:
            o["wob"] += o["wob_s"]
            o["x"]   += np.sin(o["wob"]) * o["wob_a"] * 0.06
            o["y"]   += o["speed"]
            dist = np.hypot(o["x"] - px, o["y"] - py)
            if dist < PR + o["size"] * 0.5:
                if self.shield > 0:
                    self.shield = 0
                    for _ in range(20):
                        self.particles.append(Particle(o["x"], o["y"], (20, 200, 240)))
                else:
                    self.lives -= 1
                    for _ in range(30):
                        self.particles.append(Particle(px, py, (50, 50, 200)))
                    if self.lives <= 0:
                        self.state = "dead"
                continue
            if o["y"] < GAME_H + 60:
                alive.append(o)
            else:
                self.dodge_count += 1
                self.score += 5
        self.obstacles = alive

        # Powerups
        alive_pu = []
        for pu in self.powerups:
            pu["y"] += pu["speed"]
            dist = np.hypot(pu["x"] - px, pu["y"] - py)
            if dist < PR + pu["size"]:
                self.score += pu["pts"]
                if pu["effect"] == "shield":
                    self.shield = 180
                elif pu["effect"] == "life" and self.lives < 5:
                    self.lives += 1
                for _ in range(25):
                    self.particles.append(Particle(pu["x"], pu["y"], pu["color"]))
                continue
            if pu["y"] < GAME_H + 40:
                alive_pu.append(pu)
        self.powerups = alive_pu

        # Particles
        self.particles = [p for p in self.particles if p.update()]

        if self.score >= 2000:
            self.state = "win"

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, frame):
        canvas = np.zeros((GAME_H, GAME_W, 3), dtype=np.uint8)
        canvas[:] = COLORS["bg"]

        # Fixed starfield (plain Python ints — no numpy dtype issue)
        for sx, sy, br in self.stars:
            cv2.circle(canvas, (sx, sy), 1, (br, br, br), -1)

        # Subtle grid
        for gx in range(0, GAME_W, 80):
            cv2.line(canvas, (gx, 0), (gx, GAME_H), (25, 18, 40), 1)
        for gy in range(0, GAME_H, 80):
            cv2.line(canvas, (0, gy), (GAME_W, gy), (25, 18, 40), 1)

        if self.state == "intro":
            self._draw_intro(canvas, frame)
        elif self.state in ("playing", "dead", "win"):
            self._draw_playing(canvas, frame)
            if self.state == "dead":
                self._overlay(canvas, "GAME OVER!",
                              f"Score: {self.score}   Dodges: {self.dodge_count}",
                              "SPACE = retry   Q = quit", (40, 40, 160))
            elif self.state == "win":
                self._overlay(canvas, "YOU WIN!",
                              f"Final Score: {self.score}",
                              "SPACE = play again   Q = quit", (20, 120, 60))
        return canvas

    def _draw_intro(self, canvas, frame):
        self._cam_preview(canvas, frame, 10, 10, 200, 150)
        draw_text(canvas, "NOSE",   (GAME_W // 2 - 130, 155), 3.5, (80, 200, 120), 6)
        draw_text(canvas, "DODGE!", (GAME_W // 2 - 168, 225), 3.5, (255, 180, 50), 6)
        draw_text(canvas, "Move your NOSE to control the character!",
                  (GAME_W // 2 - 270, 295), 0.8, (255, 255, 255), 1)
        draw_text(canvas, "Dodge  POOPS  BOMBS  VIRUSES",
                  (GAME_W // 2 - 200, 330), 0.8, (200, 120, 255), 1)
        draw_text(canvas, "Collect STARS (shield)  &  HEARTS (extra life)",
                  (GAME_W // 2 - 280, 365), 0.8, (80, 220, 200), 1)
        draw_text(canvas, "Reach 2000 points to WIN!",
                  (GAME_W // 2 - 175, 400), 0.9, COLORS["gold"], 2)

        mode = "MediaPipe (precise)" if MEDIAPIPE_AVAILABLE else "Haar Cascade (basic)"
        draw_text(canvas, f"Tracking: {mode}", (20, GAME_H - 55), 0.5, (140, 140, 140), 1)

        if (self.frame_count // 20) % 2 == 0:
            draw_text(canvas, ">> Press SPACE to START <<",
                      (GAME_W // 2 - 205, 468), 1.0, (255, 220, 50), 2)

        for i, o in enumerate(OBSTACLES):
            draw_symbol(canvas, o["label"], 150 + i * 180, 535, 20, o["color"])
            draw_text(canvas, o["label"], (125 + i * 180, 570),
                      0.45, o["color"], 1)
        for i, p in enumerate(POWERUPS):
            draw_symbol(canvas, p["label"], 680 + i * 60, 535, 18, p["color"])

        self.frame_count += 1

    def _draw_playing(self, canvas, frame):
        # Particles
        for p in self.particles:
            p.draw(canvas)

        # Powerups
        for pu in self.powerups:
            pulse = int(10 * abs(np.sin(self.frame_count * 0.1)))
            cv2.circle(canvas, (int(pu["x"]), int(pu["y"])),
                       pu["size"] + pulse,
                       tuple(int(c) for c in pu["color"]), 2)
            draw_symbol(canvas, pu["label"], pu["x"], pu["y"], pu["size"], pu["color"])

        # Obstacles
        for o in self.obstacles:
            sx, sy = int(o["x"]) + 4, int(o["y"]) + 4
            cv2.circle(canvas, (sx, sy), o["size"] // 2 + 4, (0, 0, 0), -1)
            draw_symbol(canvas, o["label"], o["x"], o["y"], o["size"], o["color"])

        # Player
        px, py = self.smooth_x, self.smooth_y
        if self.shield > 0:
            r = 34 + int(4 * abs(np.sin(self.frame_count * 0.15)))
            a = min(1.0, self.shield / 60)
            cv2.circle(canvas, (px, py), r,
                       (int(20 * a), int(200 * a), int(240 * a)), 3)
        draw_symbol(canvas, "PLAYER", px, py, 22, COLORS["green"])
        dot_c = (100, 255, 150) if self.shield <= 0 else (20, 220, 255)
        cv2.circle(canvas, (px, py), 5, dot_c, -1)

        self._cam_preview(canvas, frame, GAME_W - 215, 5, 210, 158)
        self._draw_hud(canvas)

    def _draw_hud(self, canvas):
        cv2.rectangle(canvas, (0, 0), (GAME_W, 55), COLORS["hud_bg"], -1)
        draw_text(canvas, f"SCORE: {self.score}",    (15,  38), 0.9, COLORS["gold"],  2)
        draw_text(canvas, f"LVL {self.level}",       (280, 38), 0.9, (150, 220, 255), 2)
        for i in range(5):
            c = (80, 60, 220) if i < self.lives else (55, 45, 65)
            draw_symbol(canvas, "HEART", 400 + i * 32, 28, 12, c)
        if self.shield > 0:
            bw = int(self.shield / 180 * 120)
            cv2.rectangle(canvas, (570, 18), (690, 36), (40, 40, 60), -1)
            cv2.rectangle(canvas, (570, 18), (570 + bw, 36), (20, 200, 240), -1)
            draw_text(canvas, "SHIELD", (575, 33), 0.45, (20, 200, 240), 1)

        draw_text(canvas, f"DODGED: {self.dodge_count}",
                  (15, GAME_H - 15), 0.55, (150, 150, 180), 1)

        pct = min(100, self.score * 100 // 2000)
        cv2.rectangle(canvas, (GAME_W // 2 - 80, GAME_H - 22),
                               (GAME_W // 2 + 80, GAME_H - 8), (40, 40, 60), -1)
        cv2.rectangle(canvas, (GAME_W // 2 - 80, GAME_H - 22),
                               (GAME_W // 2 - 80 + pct * 160 // 100, GAME_H - 8),
                               (80, 200, 120), -1)
        draw_text(canvas, f"GOAL {pct}%",
                  (GAME_W // 2 - 38, GAME_H - 10), 0.45, (255, 255, 255), 1)

    def _cam_preview(self, canvas, frame, x, y, w, h):
        if frame is None:
            return
        small = cv2.flip(cv2.resize(frame, (w, h)), 1)
        canvas[y:y + h, x:x + w] = small
        cv2.rectangle(canvas, (x - 2, y - 2), (x + w + 2, y + h + 2), (80, 80, 100), 2)
        fh, fw = frame.shape[:2]
        nx = int((1 - self.nose_x / fw) * w) + x
        ny = int(self.nose_y / fh * h)  + y
        cv2.circle(canvas, (nx, ny), 6, (0, 255, 100), -1)
        cv2.circle(canvas, (nx, ny), 9, (0, 200, 80),  2)
        draw_text(canvas, "YOU", (x + 5, y + h - 5), 0.4, (200, 200, 200), 1, shadow=False)

    def _overlay(self, canvas, title, sub, hint, color):
        dark = canvas.copy()
        cv2.rectangle(dark, (0, 0), (GAME_W, GAME_H), (0, 0, 0), -1)
        cv2.addWeighted(dark, 0.6, canvas, 0.4, 0, canvas)

        tw = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 2.2, 4)[0][0]
        draw_text(canvas, title, (GAME_W // 2 - tw // 2, GAME_H // 2 - 60),
                  2.2, COLORS["gold"], 4)
        sw = cv2.getTextSize(sub, cv2.FONT_HERSHEY_DUPLEX, 0.9, 2)[0][0]
        draw_text(canvas, sub, (GAME_W // 2 - sw // 2, GAME_H // 2 + 10),
                  0.9, (255, 255, 255), 2)
        if (self.frame_count // 25) % 2 == 0:
            hw = cv2.getTextSize(hint, cv2.FONT_HERSHEY_DUPLEX, 0.65, 1)[0][0]
            draw_text(canvas, hint, (GAME_W // 2 - hw // 2, GAME_H // 2 + 70),
                      0.65, (200, 200, 200), 1)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 52)
    print("  👃  NOSE DODGE GAME  👃")
    print("=" * 52)
    mode = "MediaPipe" if MEDIAPIPE_AVAILABLE else "Haar Cascade"
    print(f"  Tracking : {mode}")
    print("  Controls : Move your nose!   SPACE=start   Q=quit")
    print("=" * 52)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    game = NoseDodgeGame()
    cv2.namedWindow("Nose Dodge Game", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Nose Dodge Game", GAME_W, GAME_H)

    prev = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        nx, ny = game.get_nose(frame)
        if nx is not None:
            fh, fw = frame.shape[:2]
            game.nose_x = int((1 - nx / fw) * GAME_W)
            game.nose_y = max(60, min(GAME_H - 60, int(ny / fh * GAME_H * 1.3)))

        game.update()
        canvas = game.draw(frame)

        # FPS
        now  = time.time()
        fps  = 1.0 / max(0.001, now - prev)
        prev = now
        draw_text(canvas, f"FPS:{fps:.0f}", (GAME_W - 80, GAME_H - 15),
                  0.45, (80, 80, 100), 1)

        cv2.imshow("Nose Dodge Game", canvas)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break
        elif key == ord(' '):
            if game.state == "intro":
                game.state = "playing"
            elif game.state in ("dead", "win"):
                game.reset()
                game.state = "playing"

    cap.release()
    cv2.destroyAllWindows()
    print("Thanks for playing Nose Dodge! 👃")


if __name__ == "__main__":
    main()
