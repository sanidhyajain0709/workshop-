"""
📸 Photo Block Puzzle Game
--------------------------
Take a photo with your webcam, then solve the sliding tile puzzle!

Controls:
  SPACE / ENTER  – Capture photo (on camera screen)
  R              – Retry / take new photo
  Arrow Keys     – Move the blank tile (slide puzzle)
  H              – Show hint (highlight a misplaced tile)
  ESC / Q        – Quit

Requirements:
  pip install opencv-python numpy
"""

import sys
import time
import random
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

# ── Configuration ──────────────────────────────────────────────────────────────

GRID      = 4      # change to 3 (easier) or 5 (harder)
WIN_SIZE  = 640
TILE_SIZE = WIN_SIZE // GRID
SHUFFLE_N = 200
CAM_W, CAM_H = 640, 480
FONT = cv2.FONT_HERSHEY_SIMPLEX

# ── Colour palette ─────────────────────────────────────────────────────────────

class Color:
    BG      = ( 30,  30,  30)
    BORDER  = (200, 200, 200)
    BLANK   = ( 50,  50,  50)
    WIN_BG  = ( 20, 120,  20)
    HINT    = (  0, 220, 255)
    TEXT    = (255, 255, 255)
    HUD     = ( 20,  20,  20)
    CAPTURE = (  0, 255, 100)
    TIMER   = (  0, 100, 255)

# ── Types & constants ──────────────────────────────────────────────────────────

TileMap = dict[tuple[int, int], np.ndarray]
State   = list[int]

BLANK_ID = GRID * GRID - 1

# Arrow keys + WASD  →  (Δrow, Δcol)
DIRECTIONS: dict[int, tuple[int, int]] = {
    82: (-1,  0),  # ↑
    84: ( 1,  0),  # ↓
    81: ( 0, -1),  # ←
    83: ( 0,  1),  # →
    ord('w'): (-1,  0),
    ord('s'): ( 1,  0),
    ord('a'): ( 0, -1),
    ord('d'): ( 0,  1),
}

# ── Puzzle logic ───────────────────────────────────────────────────────────────

def slice_tiles(img: np.ndarray) -> TileMap:
    """Slice *img* into GRID×GRID tiles, keyed by (row, col)."""
    h, w = img.shape[:2]
    th, tw = h // GRID, w // GRID
    return {
        (r, c): img[r * th:(r + 1) * th, c * tw:(c + 1) * tw].copy()
        for r in range(GRID)
        for c in range(GRID)
    }


def solved_state() -> State:
    return list(range(GRID * GRID))


def blank_rc(state: State) -> tuple[int, int]:
    return divmod(state.index(BLANK_ID), GRID)


def apply_move(state: State, dr: int, dc: int) -> Optional[State]:
    """Slide the neighbour tile into the blank; return new state or None."""
    r, c = blank_rc(state)
    nr, nc = r + dr, c + dc
    if not (0 <= nr < GRID and 0 <= nc < GRID):
        return None
    new = state[:]
    new[r * GRID + c], new[nr * GRID + nc] = new[nr * GRID + nc], new[r * GRID + c]
    return new


def shuffle(state: State, n: int = SHUFFLE_N) -> State:
    """Shuffle by n random valid moves, avoiding immediate reversal."""
    cardinals = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    last_reverse: Optional[tuple[int, int]] = None
    for _ in range(n):
        random.shuffle(cardinals)
        for d in cardinals:
            if d == last_reverse:
                continue
            ns = apply_move(state, *d)
            if ns:
                state        = ns
                last_reverse = (-d[0], -d[1])
                break
    return state


def is_solved(state: State) -> bool:
    return state == solved_state()

# ── Drawing ────────────────────────────────────────────────────────────────────

def _dim(canvas: np.ndarray, y1: int, y2: int, x1: int, x2: int, alpha: float = 0.75) -> None:
    roi = canvas[y1:y2, x1:x2]
    cv2.addWeighted(roi, alpha, np.zeros_like(roi), 1 - alpha, 0, roi)


def draw_puzzle(
    state: State,
    tiles: TileMap,
    hint_tile: Optional[int],
    elapsed: float,
    moves: int,
) -> np.ndarray:
    ts     = TILE_SIZE
    canvas = np.full((WIN_SIZE, WIN_SIZE, 3), Color.BG, dtype=np.uint8)

    for pos, tile_id in enumerate(state):
        r, c       = divmod(pos, GRID)
        y1, y2     = r * ts, (r + 1) * ts
        x1, x2     = c * ts, (c + 1) * ts

        if tile_id == BLANK_ID:
            cv2.rectangle(canvas, (x1, y1), (x2, y2), Color.BLANK, -1)
        else:
            tr, tc = divmod(tile_id, GRID)
            canvas[y1:y2, x1:x2] = cv2.resize(tiles[(tr, tc)], (ts, ts))
            if tile_id != pos:
                _dim(canvas, y1, y2, x1, x2)
            if hint_tile == tile_id:
                cv2.rectangle(canvas, (x1, y1), (x2, y2), Color.HINT, 4)

        cv2.rectangle(canvas, (x1, y1), (x2, y2), Color.BORDER, 1)

    # HUD strip
    hud_y = WIN_SIZE - 30
    cv2.rectangle(canvas, (0, hud_y), (WIN_SIZE, WIN_SIZE), Color.HUD, -1)
    cv2.putText(
        canvas,
        f"Moves: {moves}   Time: {int(elapsed)}s"
        "   [Arrows]=slide  [H]=hint  [R]=new photo  [Q]=quit",
        (8, WIN_SIZE - 10), FONT, 0.42, Color.TEXT, 1, cv2.LINE_AA,
    )
    return canvas


def draw_win_overlay(canvas: np.ndarray, moves: int, elapsed: float) -> np.ndarray:
    overlay = canvas.copy()
    cv2.rectangle(overlay, (80, 200), (WIN_SIZE - 80, WIN_SIZE - 200), Color.WIN_BG, -1)
    cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)

    labels = [
        ("PUZZLE SOLVED!",                        (140, 280), 1.1, (255, 255, 100), 2),
        (f"Moves : {moves}",                      (220, 335), 0.7, Color.TEXT,      1),
        (f"Time  : {int(elapsed)}s",              (220, 370), 0.7, Color.TEXT,      1),
        ("Press R for a new photo  |  Q to quit", (105, 425), 0.52, (200, 200, 200), 1),
    ]
    for text, pos, scale, color, thickness in labels:
        cv2.putText(canvas, text, pos, FONT, scale, color, thickness, cv2.LINE_AA)

    return canvas

# ── Camera capture ─────────────────────────────────────────────────────────────

def capture_photo() -> np.ndarray:
    """Display webcam feed with grid overlay; return the captured frame."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("[ERROR] Cannot open webcam. Make sure a camera is connected.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

    win = "📸  Photo Puzzle — Camera"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, CAM_W, CAM_H)

    countdown_start: Optional[float] = None
    captured: Optional[np.ndarray]   = None

    while captured is None:
        ret, frame = cap.read()
        if not ret:
            continue

        display = frame.copy()

        # grid preview lines
        for i in range(1, GRID):
            x, y = i * (CAM_W // GRID), i * (CAM_H // GRID)
            cv2.line(display, (x, 0), (x, CAM_H), (0, 200, 0), 1)
            cv2.line(display, (0, y), (CAM_W, y), (0, 200, 0), 1)

        if countdown_start is None:
            cv2.putText(display,
                        "Position subject & press SPACE or ENTER to capture",
                        (10, 30), FONT, 0.6, Color.CAPTURE, 2, cv2.LINE_AA)
            cv2.putText(display, f"Grid: {GRID}x{GRID}  |  Q=quit",
                        (10, CAM_H - 12), FONT, 0.5, (200, 200, 200), 1)
        else:
            remaining = 3 - int(time.time() - countdown_start)
            if remaining <= 0:
                captured = frame.copy()
            else:
                cv2.putText(display, str(remaining),
                            (CAM_W // 2 - 30, CAM_H // 2 + 20),
                            FONT, 4.0, Color.TIMER, 6, cv2.LINE_AA)

        cv2.imshow(win, display)

        key = cv2.waitKey(30) & 0xFF
        if key in (ord(' '), 13):           # SPACE or ENTER
            countdown_start = time.time()
        elif key in (ord('q'), ord('Q'), 27):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)

    cap.release()
    cv2.destroyAllWindows()
    return captured

# ── Game state (dataclass) ─────────────────────────────────────────────────────

@dataclass
class GameState:
    state:      State
    tiles:      TileMap
    moves:      int             = 0
    start_time: float           = field(default_factory=time.time)
    hint_tile:  Optional[int]   = None
    hint_until: float           = 0.0
    solved:     bool            = False

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    def try_move(self, dr: int, dc: int) -> None:
        if self.solved:
            return
        ns = apply_move(self.state, dr, dc)
        if ns:
            self.state  = ns
            self.moves += 1
            self.solved = is_solved(self.state)

    def show_hint(self) -> None:
        for pos, tid in enumerate(self.state):
            if tid != pos and tid != BLANK_ID:
                self.hint_tile  = tid
                self.hint_until = time.time() + 2.0
                return

    def expire_hint(self) -> None:
        if self.hint_tile is not None and time.time() > self.hint_until:
            self.hint_tile = None

    def render(self) -> np.ndarray:
        canvas = draw_puzzle(self.state, self.tiles,
                             self.hint_tile, self.elapsed, self.moves)
        if self.solved:
            canvas = draw_win_overlay(canvas, self.moves, self.elapsed)
        return canvas

# ── Main game loop ─────────────────────────────────────────────────────────────

def run_game(photo: np.ndarray) -> bool:
    """Run one puzzle session. Returns True if player wants a new photo."""
    gs = GameState(
        state=shuffle(solved_state()),
        tiles=slice_tiles(cv2.resize(photo, (WIN_SIZE, WIN_SIZE))),
    )

    win = f"📷  Photo Block Puzzle  ({GRID}×{GRID})"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, WIN_SIZE, WIN_SIZE)

    while True:
        gs.expire_hint()
        cv2.imshow(win, gs.render())
        key = cv2.waitKey(30) & 0xFF

        if key in (ord('q'), ord('Q'), 27):
            cv2.destroyAllWindows()
            return False

        if key in (ord('r'), ord('R')):
            cv2.destroyAllWindows()
            return True

        if key in (ord('h'), ord('H')):
            gs.show_hint()

        elif key in DIRECTIONS:
            gs.try_move(*DIRECTIONS[key])

# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  📸  Photo Block Puzzle Game")
    print("=" * 60)
    print(f"  Grid         : {GRID}×{GRID}")
    print(f"  Shuffle moves: {SHUFFLE_N}")
    print()
    print("  Controls:")
    print("    SPACE / ENTER  – Capture photo")
    print("    Arrow Keys     – Slide tiles")
    print("    H              – Hint")
    print("    R              – New photo")
    print("    Q / ESC        – Quit")
    print("=" * 60)

    while True:
        photo = capture_photo()
        if not run_game(photo):
            break

    print("\nThanks for playing! 👋")


if __name__ == "__main__":
    main()
