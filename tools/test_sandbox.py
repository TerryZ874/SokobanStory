#!/usr/bin/env python3
"""
Sandbox Sokoban Level Validator
Tests 6 hand-crafted puzzles with BFS to verify solvability.
"""
import sys
sys.path.insert(0, 'tools')
from bfs_solver import solve, validate_level

# ─── S1: L型转弯 (L-shaped turn) ──────────────────────────────────────────
# Concept: L-shaped wall blocks direct up-then-right path.
# Box must first be pushed RIGHT (away from target), then UP around the corner.
# Grid: 8 cols x 5 rows
# . . . . . . . .
# . . W W W . . .
# . . . . W . . .
# . . B . . . . .
# . . . P . . . .
# Walls: (2,1),(3,1),(4,1),(4,2) — L-shape in top-right area
S1 = {
    "id": "S1",
    "name": "S1 - L型转弯",
    "cols": 8,
    "rows": 5,
    "step_limit": 25,
    "grid": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 0, 0, 0, 0],
    ],
    "targets": [[5, 2]],
}

# ─── S2: 推箱顺序 (Push Order) ────────────────────────────────────────────
# Concept: Box A's starting position IS Box B's target. Box A must be
# pushed away BEFORE Box B can reach its target. Pushing Box B anywhere
# first doesn't help because Box A blocks the target.
# Grid: 8 cols x 7 rows
# . . . . . . . .
# . W W . W W . .
# . . . . . . . .
# . . . . . . . .
# . . A . . B . .
# . . . . . . . .
# . . . P . . . .
S2 = {
    "id": "S2",
    "name": "S2 - 推箱顺序",
    "cols": 8,
    "rows": 7,
    "step_limit": 30,
    "grid": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 0, 0, 0, 0],
    ],
    "targets": [[2, 2], [2, 4]],
}

# ─── S3: 死胡同 (Dead End) ────────────────────────────────────────────────
# Concept: Two boxes in a corridor with an alcove. Box A sits deep,
# Box B is at the entrance. If you push Box A into the alcove first,
# Box B blocks the exit and Box A is trapped. Must push Box B out
# of the way first, then free Box A, then place both.
# Grid: 8 cols x 6 rows
# . . . . . . . .
# . W W W . . . .
# . . . W . . . .
# . . . W . . . .
# . B . . . B . .
# . . . P . . . .
S3 = {
    "id": "S3",
    "name": "S3 - 死胡同",
    "cols": 8,
    "rows": 6,
    "step_limit": 35,
    "grid": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 3, 0, 0, 0, 0],
    ],
    "targets": [[1, 2], [5, 1]],
}

# ─── S4: 窄路相逢 (Narrow Corridor) ────────────────────────────────────────
# Concept: Three boxes, two wall pillars with a 1-tile-wide gap at col 3.
# Boxes come from both sides and must take turns passing through the gap.
# Like a single-lane bridge.
# Grid: 8 cols x 7 rows
# . . . . . . . .
# . W W . W W . .
# . . . . . . . .
# . B B . B . . .
# . . . . . . . .
# . . . . . . . .
# . . . P . . . .
S4 = {
    "id": "S4",
    "name": "S4 - 窄路相逢",
    "cols": 8,
    "rows": 7,
    "step_limit": 45,
    "grid": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 0, 0, 0, 0],
    ],
    "targets": [[1, 2], [3, 2], [5, 2]],
}

# ─── S5: 交叉路口 (T-Junction) ────────────────────────────────────────────
# Concept: L-shaped wall creates a T-junction effect. Three boxes
# approach from different sides and must go through a central axis.
# Grid: 8 cols x 7 rows
# . . . . . . . .
# . . W W W . . .
# . . . . W . . .
# . . . . . . . .
# . B . . . . B .
# . . . . . . . .
# . . . P . . . .
S5 = {
    "id": "S5",
    "name": "S5 - 交叉路口",
    "cols": 8,
    "rows": 7,
    "step_limit": 40,
    "grid": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 0, 0, 0, 0],
    ],
    "targets": [[0, 2], [5, 1], [6, 3]],
}

# ─── S6: 多方调度 (Multi-Room) ────────────────────────────────────────────
# Concept: Four boxes in two connected rooms with narrow passages.
# Boxes must be shuttled between rooms in order.
# Grid: 9 cols x 8 rows
# . . . . . . . . .
# . W W W . W W . .
# . . . W . . W . .
# . . . W . . . . .
# . B . . . B . . .
# . . . . . . . . .
# . . B . . . B . .
# . . . P . . . . .
S6 = {
    "id": "S6",
    "name": "S6 - 多方调度",
    "cols": 9,
    "rows": 8,
    "step_limit": 60,
    "grid": [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 3, 0, 0, 0, 0, 0],
    ],
    "targets": [[0, 3], [4, 1], [4, 6], [7, 3]],
}

# ─── Run verification ──────────────────────────────────────────────────────
ALL_LEVELS = [S1, S2, S3, S4, S5, S6]

def print_grid(grid, targets=None, boxes=None):
    """Pretty-print a grid with optional overlay."""
    chars = {0: '.', 1: '#', 2: '$', 3: '@'}
    for y, row in enumerate(grid):
        line = ""
        for x, cell in enumerate(row):
            if targets and [x, y] in targets:
                line += 'X'  # target indicator
            elif cell == 2:
                line += '$'
            elif cell == 3:
                line += '@'
            elif cell == 1:
                line += '#'
            else:
                line += '.'
        print(line)

def main():
    all_ok = True
    for level in ALL_LEVELS:
        lid = level["id"]
        name = level["name"]
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"{'='*60}")
        print(f"  Size: {level['cols']}x{level['rows']}")
        print(f"  Boxes: {sum(row.count(2) for row in level['grid'])}")
        print(f"  Targets: {level['targets']}")
        print(f"\n  Grid:")
        print_grid(level["grid"])

        solvable, min_steps, error = validate_level(level)

        if solvable:
            print(f"\n  >> SOLVABLE: min_steps = {min_steps}")
        else:
            print(f"\n  >> FAIL: {error}")
            all_ok = False

    print(f"\n{'='*60}")
    if all_ok:
        print("  ALL 6 PUZZLES ARE SOLVABLE!")
    else:
        print(f"  SOME PUZZLES FAILED - check output above")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
