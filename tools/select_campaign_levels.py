#!/usr/bin/env python3
"""
Select 20 community levels from pool files for the story campaign.
Progressive difficulty: 1box→6box, BFS-verified solvable.
Generates data/levels.json
"""
import json
import sys
import os
from collections import deque

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]
POOL_DIR = "data/pools"

# Story names for each level
CHAPTER_NAMES = [
    "第一关：初识推箱",
    "第二关：U 形弯",
    "第三关：双箱协作",
    "第四关：转角遇到箱",
    "第五关：一推到底",
    "第六关：双箱上推",
    "第七关：向右看齐",
    "第八关：T 形路",
    "第九关：迂回",
    "第十关：三角阵",
    "第十一关：通道",
    "第十二关：三足鼎立",
    "第十三关：竞技场",
    "第十四关：多段推进",
    "第十五关：四箱入门",
    "第十六关：算力激增",
    "第十七关：四面出击",
    "第十八关：算力风暴",
    "第十九关：黎明之前",
    "第二十关：终局之战",
]

# Progressive box count per chapter
CHAPTER_BOXES = [1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6]


def bfs_solve(level):
    """Returns min steps or None if unsolvable."""
    rows, cols = level['rows'], level['cols']
    grid = [list(r) for r in level['grid']]
    targets = [(t[0], t[1]) for t in level['targets']]
    target_set = set(targets)

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
    if player_start is None:
        return None
    boxes_start.sort()

    walls = set()
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == 1:
                walls.add((x, y))

    # Deadlock precompute
    dead = set()
    for y in range(rows):
        for x in range(cols):
            if (x, y) in walls or (x, y) in target_set:
                continue
            up = (x, y - 1) in walls
            down = (x, y + 1) in walls
            left = (x - 1, y) in walls
            right = (x + 1, y) in walls
            if (up and left) or (up and right) or (down and left) or (down and right):
                dead.add((x, y))

    start_boxes = tuple(boxes_start)
    q = deque()
    q.append((player_start, start_boxes, 0))
    visited = {(player_start, start_boxes)}

    max_states = 5_000_000
    states = 0

    while q:
        (px, py), boxes_tuple, steps = q.popleft()
        boxes = list(boxes_tuple)

        if all(b in target_set for b in boxes):
            return steps

        states += 1
        if states > max_states:
            return None

        box_set = set(boxes)
        for dx, dy in DIRS:
            nx, ny = px + dx, py + dy
            if nx < 0 or nx >= cols or ny < 0 or ny >= rows:
                continue
            if (nx, ny) in walls:
                continue
            if (nx, ny) in box_set:
                bx, by = nx + dx, ny + dy
                if bx < 0 or bx >= cols or by < 0 or by >= rows:
                    continue
                if (bx, by) in walls or (bx, by) in box_set:
                    continue
                if (bx, by) not in target_set and (bx, by) in dead:
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
                new_state = ((nx, ny), boxes_tuple)
                if new_state not in visited:
                    visited.add(new_state)
                    q.append(((nx, ny), boxes_tuple, steps + 1))

    return None


def load_pool(box_count):
    fpath = os.path.join(POOL_DIR, f"pool_{box_count}box.json")
    with open(fpath) as f:
        return json.load(f)["levels"]


def find_candidates(pool_levels, max_cells=120, prefer_sources=None):
    """Find good candidates: reasonable size, diverse sources."""
    candidates = []
    for lv in pool_levels:
        if lv["cells"] > max_cells:
            continue
        if lv["cols"] > 20 or lv["rows"] > 20:
            continue
        candidates.append(lv)

    # Sort by cells (ascending) for predictability
    candidates.sort(key=lambda x: (x["cells"], x["source"], x["num"]))

    # Deduplicate by grid hash
    seen_grids = set()
    unique = []
    for lv in candidates:
        gh = str(lv["grid"])
        if gh not in seen_grids:
            seen_grids.add(gh)
            unique.append(lv)

    return unique


def pick_levels(box_count, count_needed, candidates):
    """BFS verify and pick levels."""
    picked = []
    for lv in candidates:
        if len(picked) >= count_needed:
            break

        steps = bfs_solve(lv)
        if steps is None:
            print(f"    ✗ UNSOLVABLE: {lv['source']}#{lv['num']} ({lv['title']}) - {lv['cells']}c")
            continue

        print(f"    ✓ {lv['source']}#{lv['num']} \"{lv['title']}\" — {lv['cells']}c ({lv['cols']}x{lv['rows']}), BFS={steps}")
        picked.append({
            "source": lv["source"],
            "num": lv["num"],
            "title": lv["title"],
            "author": lv["author"],
            "cols": lv["cols"],
            "rows": lv["rows"],
            "cells": lv["cells"],
            "boxes": lv["boxes"],
            "step_limit": max(steps * 2, lv["step_limit"]),
            "grid": lv["grid"],
            "targets": lv["targets"],
            "bfs_steps": steps,
        })

    return picked


def main():
    print("Selecting 20 campaign levels from community pools...\n")

    all_picked = []

    # Distribution of levels per box count
    # Count how many of each box count we need
    from collections import Counter
    needed = Counter(CHAPTER_BOXES)

    for box_count in sorted(needed.keys()):
        count_needed = needed[box_count]
        print(f"\n--- {box_count}箱 (need {count_needed}) ---")

        pool = load_pool(box_count)
        candidates = find_candidates(pool)

        if not candidates:
            print(f"  ERROR: No candidates for {box_count} box!")
            sys.exit(1)

        print(f"  {len(candidates)} candidates (≤120 cells)")
        picked = pick_levels(box_count, count_needed, candidates)

        if len(picked) < count_needed:
            print(f"  ERROR: Only found {len(picked)}/{count_needed} solvable {box_count}-box levels!")
            sys.exit(1)

        all_picked.extend(picked)

    # Build levels.json
    output_levels = []
    for i, lv in enumerate(all_picked):
        lid = i + 1
        output_levels.append({
            "id": lid,
            "name": CHAPTER_NAMES[i],
            "cols": lv["cols"],
            "rows": lv["rows"],
            "step_limit": lv["step_limit"],
            "grid": lv["grid"],
            "targets": lv["targets"],
        })

    output = {"levels": output_levels}

    with open("data/levels.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Generated data/levels.json with {len(output_levels)} levels")
    print(f"\nLevel summary:")
    for lv in output_levels:
        box_count = sum(row.count(2) for row in lv["grid"])
        print(f"  L{lv['id']:2d} | {box_count}箱 | {lv['cols']}x{lv['rows']} | limit={lv['step_limit']} | {lv['name']}")


if __name__ == "__main__":
    main()
