#!/usr/bin/env python3
"""
BFS Sokoban solver with deadlock detection.
Validates levels and finds minimum steps.
"""

import json
import sys
from collections import deque

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # up, down, left, right


def _precompute_deadlocks(walls, targets_set, cols, rows):
    """
    Precompute deadlock positions.
    Only corner deadlocks: walls on two perpendicular sides = box can never escape.
    Tunnel deadlocks are NOT included (too aggressive, can false-positive).
    """
    deadlocks = set()

    for y in range(rows):
        for x in range(cols):
            if (x, y) in walls or (x, y) in targets_set:
                continue

            up = (x, y - 1) in walls
            down = (x, y + 1) in walls
            left = (x - 1, y) in walls
            right = (x + 1, y) in walls

            # Corner: two perpendicular walls
            if (up and left) or (up and right) or (down and left) or (down and right):
                deadlocks.add((x, y))

    return deadlocks


def solve(level):
    """
    BFS solver counting every player move (walk + push) as one step.
    Uses deadlock detection to prune unsolvable branches.

    Returns (min_steps) or None if unsolvable.
    """
    rows, cols = level['rows'], level['cols']
    grid = [list(r) for r in level['grid']]
    targets = [(t[0], t[1]) for t in level['targets']]
    target_set = set(targets)

    # Find initial player and box positions
    player_start = None
    boxes_start = []
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == 3:
                player_start = (x, y)
                grid[y][x] = 0
            elif grid[y][x] == 2:
                boxes_start.append((x, y))
                grid[y][x] = 0

    assert player_start is not None, "No player found"
    boxes_start.sort()

    # Precompute walls
    walls = set()
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == 1:
                walls.add((x, y))

    deadlock_positions = _precompute_deadlocks(walls, target_set, cols, rows)

    # BFS over (player_pos, boxes_tuple)
    start_boxes = tuple(boxes_start)
    q = deque()
    q.append((player_start, start_boxes, 0))
    visited = {(player_start, start_boxes)}

    max_states = 50_000_000
    states_explored = 0

    while q:
        (px, py), boxes_tuple, steps = q.popleft()
        boxes = list(boxes_tuple)

        # Win check
        if all(b in target_set for b in boxes):
            return steps

        states_explored += 1
        if states_explored > max_states:
            return None

        box_set = set(boxes)

        for dx, dy in DIRS:
            nx, ny = px + dx, py + dy

            if nx < 0 or nx >= cols or ny < 0 or ny >= rows:
                continue
            if (nx, ny) in walls:
                continue

            if (nx, ny) in box_set:
                # Push box
                bx, by = nx + dx, ny + dy

                if bx < 0 or bx >= cols or by < 0 or by >= rows:
                    continue
                if (bx, by) in walls or (bx, by) in box_set:
                    continue

                # Deadlock check: is the new box position dead?
                if (bx, by) not in target_set and (bx, by) in deadlock_positions:
                    continue

                new_boxes = list(boxes)
                idx = new_boxes.index((nx, ny))
                new_boxes[idx] = (bx, by)
                new_boxes.sort()
                new_state = ((nx, ny), tuple(new_boxes))

                if new_state not in visited:
                    visited.add(new_state)
                    q.append(((nx, ny), tuple(new_boxes), steps + 1))
            else:
                # Walk
                new_state = ((nx, ny), boxes_tuple)
                if new_state not in visited:
                    visited.add(new_state)
                    q.append(((nx, ny), boxes_tuple, steps + 1))

    return None  # Unsolvable


def validate_level(level):
    """Validate a level and return (solvable, min_steps, error)."""
    rows, cols = level['rows'], level['cols']
    grid = level['grid']

    if len(grid) != rows:
        return False, None, f"Grid rows={len(grid)} != declared rows={rows}"
    for r in grid:
        if len(r) != cols:
            return False, None, f"Row length {len(r)} != declared cols={cols}"

    player_count = sum(row.count(3) for row in grid)
    box_count = sum(row.count(2) for row in grid)
    target_count = len(level['targets'])

    if player_count != 1:
        return False, None, f"Player count = {player_count}, expected 1"
    if box_count != target_count:
        return False, None, f"Box count {box_count} != target count {target_count}"

    for tx, ty in level['targets']:
        if ty < 0 or ty >= rows or tx < 0 or tx >= cols:
            return False, None, f"Target ({tx},{ty}) out of bounds"
        if grid[ty][tx] == 1:
            return False, None, f"Target ({tx},{ty}) is on a wall"

    # Check targets aren't completely walled in
    for tx, ty in level['targets']:
        accessible = False
        for ddx, ddy in DIRS:
            ax, ay = tx + ddx, ty + ddy
            if 0 <= ax < cols and 0 <= ay < rows and grid[ay][ax] != 1:
                accessible = True
                break
        if not accessible:
            return False, None, f"Target ({tx},{ty}) is completely walled in"

    result = solve(level)
    if result is None:
        return False, None, "Unsolvable or too complex"
    return True, result, None


def main():
    if len(sys.argv) < 2:
        print("Usage: bfs_solver.py <levels.json> [level_id]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    levels = data.get('levels', [])

    if len(sys.argv) >= 3:
        level_id = int(sys.argv[2])
        levels = [l for l in levels if l['id'] == level_id]
        if not levels:
            print(f"Level {level_id} not found")
            sys.exit(1)

    all_ok = True
    for level in levels:
        lid = level['id']
        solvable, min_steps, error = validate_level(level)
        if solvable:
            print(f"Level {lid:4d}: Solvable, min_steps={min_steps}")
        else:
            print(f"Level {lid:4d}: FAIL - {error}")
            all_ok = False

    if not all_ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
