#!/usr/bin/env python3
"""
Complete campaign builder: score → select → build levels.json
Uses BFS for difficulty scoring, then selects 1000 levels:
  - Levels 1-100:  Story mode, ≤5 boxes, wave difficulty 1-7
  - Levels 101-1000: Challenge mode, ≤15 boxes, progressive difficulty 4-10
"""
import json
import os
import sys
import math
import time
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

POOL_DIR = "data/pools/small"
CACHE_FILE = "data/pools/scored_levels.json"
META_FILE = "data/levels_meta.json"
OUTPUT_FILE = "data/levels.json"


# ── BFS solver with configurable state limit ──────────────────────────

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]


def _deadlocks(walls, targets_set, cols, rows):
    dead = set()
    for y in range(rows):
        for x in range(cols):
            if (x, y) in walls or (x, y) in targets_set:
                continue
            up = (x, y - 1) in walls
            down = (x, y + 1) in walls
            left = (x - 1, y) in walls
            right = (x + 1, y) in walls
            if (up and left) or (up and right) or (down and left) or (down and right):
                dead.add((x, y))
    return dead


def bfs_solve_detailed(level, max_states=50_000_000):
    """BFS solver returning {"steps": N, "states": N} or None."""
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

    dead = _deadlocks(walls, target_set, cols, rows)

    start_boxes = tuple(boxes_start)
    q = deque()
    q.append((player_start, start_boxes, 0))
    visited = {(player_start, start_boxes)}

    explored = 0
    while q:
        (px, py), boxes_tuple, steps = q.popleft()
        boxes = list(boxes_tuple)

        if all(b in target_set for b in boxes):
            return {"steps": steps, "states": explored}

        explored += 1
        if explored > max_states:
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
                ns = ((nx, ny), tuple(new_boxes))
                if ns not in visited:
                    visited.add(ns)
                    q.append(((nx, ny), tuple(new_boxes), steps + 1))
            else:
                ns = ((nx, ny), boxes_tuple)
                if ns not in visited:
                    visited.add(ns)
                    q.append(((nx, ny), boxes_tuple, steps + 1))
    return None


# ── Phase 1: Score all small-pool levels ──────────────────────────────

TIER_LIMITS = {
    3: 2_000_000,     # 1-3 box: generous (small state space, fast)
    4: 200_000,       # 4 boxes: moderate
    5: 50_000,        # 5 boxes: quick — hard ones fall to heuristic
    8: 20_000,        # 6-8 boxes: minimal
    15: 10_000,       # 9-15 boxes: very quick, heuristic for hard ones
}


def get_state_limit(boxes):
    for limit_boxes, limit in sorted(TIER_LIMITS.items()):
        if boxes <= limit_boxes:
            return limit
    return 100_000


def load_all_pool_levels(max_boxes=15):
    all_levels = []
    for i in range(1, max_boxes + 1):
        path = os.path.join(POOL_DIR, f"pool_{i}box.json")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            data = json.load(f)
        levels = data if isinstance(data, list) else data.get("levels", [])
        for lv in levels:
            lv["_boxes"] = i
        all_levels.extend(levels)
        print(f"  pool_{i}box.json: {len(levels)} levels")
    return all_levels


def structural_metrics(lv):
    grid, rows, cols = lv["grid"], lv["rows"], lv["cols"]
    walls = set()
    empty = 0
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == 1:
                walls.add((x, y))
            else:
                empty += 1

    boxes = lv.get("_boxes", 0)
    crowdedness = boxes / empty if empty > 0 else 1.0

    target_set = set((t[0], t[1]) for t in lv.get("targets", []))
    deadlock_cells = 0
    interior = 0
    for y in range(1, rows - 1):
        for x in range(1, cols - 1):
            if (x, y) in walls or (x, y) in target_set:
                continue
            interior += 1
            up = (x, y - 1) in walls
            down = (x, y + 1) in walls
            left = (x - 1, y) in walls
            right = (x + 1, y) in walls
            if (up and left) or (up and right) or (down and left) or (down and right):
                deadlock_cells += 1

    return {
        "crowdedness": round(crowdedness, 4),
        "deadlock_rate": round(deadlock_cells / interior, 4) if interior > 0 else 0,
        "empty_cells": empty,
    }


def compute_difficulty(bfs_result, metrics, boxes):
    steps = bfs_result["steps"]
    states = bfs_result["states"]
    ratio = steps / max(boxes, 1)

    if ratio <= 4:       s_step = 0
    elif ratio <= 8:     s_step = 1
    elif ratio <= 14:    s_step = 2
    elif ratio <= 22:    s_step = 3
    else:                s_step = 4

    if states <= 2000:       s_state = 0
    elif states <= 50000:    s_state = 1
    else:                    s_state = 2

    c = metrics["crowdedness"]
    s_crowd = 0 if c <= 0.06 else (1 if c <= 0.15 else 2)

    d = metrics["deadlock_rate"]
    s_dead = 0 if d <= 0.05 else (1 if d <= 0.15 else 2)

    return min(10, s_step + s_state + s_crowd + s_dead)


def heuristic_difficulty(metrics, boxes):
    """Difficulty estimate when BFS can't solve."""
    s_crowd = min(2, int(metrics["crowdedness"] * 12))
    s_dead = min(2, int(metrics["deadlock_rate"] * 10))
    box_bonus = min(4, boxes // 3)
    return min(10, box_bonus + s_crowd + s_dead + 1)


def score_level(lv):
    boxes = lv.get("_boxes", 0)
    metrics = structural_metrics(lv)
    state_limit = get_state_limit(boxes)
    cells = lv["rows"] * lv["cols"]

    bfs_result = None
    if cells <= 500:
        t0 = time.time()
        result = bfs_solve_detailed(lv, state_limit)
        dt = time.time() - t0
        if result is not None:
            bfs_result = result
        # If BFS didn't solve within limit, that's ok — use heuristic

    if bfs_result:
        difficulty = compute_difficulty(bfs_result, metrics, boxes)
    else:
        difficulty = heuristic_difficulty(metrics, boxes)

    return {
        "bfs_steps": bfs_result["steps"] if bfs_result else None,
        "bfs_states": bfs_result["states"] if bfs_result else None,
        "difficulty": difficulty,
        "boxes": boxes,
        "cols": lv["cols"],
        "rows": lv["rows"],
        "grid": lv["grid"],
        "targets": lv["targets"],
    }


def phase1_score():
    print("=" * 60)
    print("Phase 1: Scoring all small-pool levels with BFS...")
    print("=" * 60)

    all_levels = load_all_pool_levels()
    print(f"\nTotal levels: {len(all_levels)}")

    scored = []
    t_start = time.time()
    for i, lv in enumerate(all_levels):
        if i % 1000 == 0:
            elapsed = time.time() - t_start
            rate = i / elapsed if elapsed > 0 else 0
            print(f"  [{i}/{len(all_levels)}] {rate:.0f}/s, elapsed={elapsed:.0f}s")

        s = score_level(lv)
        s["pool_idx"] = i
        scored.append(s)

        # Checkpoint every 5000
        if i > 0 and i % 5000 == 0:
            with open(CACHE_FILE + ".tmp", "w") as f:
                json.dump(scored, f)

    with open(CACHE_FILE, "w") as f:
        json.dump(scored, f, indent=2)

    elapsed = time.time() - t_start
    solvable = sum(1 for s in scored if s["bfs_steps"] is not None)
    print(f"\nScored {len(scored)} levels in {elapsed:.0f}s → {CACHE_FILE}")
    print(f"  BFS solvable: {solvable}")
    print(f"  Heuristic only: {len(scored) - solvable}")
    return scored


def phase1_load_or_score():
    if os.path.exists(CACHE_FILE):
        print(f"Loading cached scores from {CACHE_FILE}")
        with open(CACHE_FILE) as f:
            data = json.load(f)
        print(f"  {len(data)} levels loaded")
        return data
    return phase1_score()


# ── Phase 2: Select levels ───────────────────────────────────────────

def build_wave_targets(n=97, lo=1, hi=7):
    """Wave difficulty curve: 4 crests across 97 levels."""
    crests = [16, 38, 62, 85]
    targets = []
    for i in range(n):
        pos = i + 1
        diff = lo
        for c in crests:
            dist = abs(pos - c)
            d = hi - max(0, dist // 5)
            diff = max(diff, min(hi, d))
        wave = math.sin(pos * math.pi / 7) * 0.5
        targets.append(max(lo, min(hi, round(diff + wave))))
    return targets


def select_story_levels(scored, preserved_levels):
    """Select 100 levels for story mode. Keep 1-3, pick 4-100."""
    preserved = []
    for lv in preserved_levels:
        preserved.append({
            "id": lv["id"], "name": lv["name"],
            "cols": lv["cols"], "rows": lv["rows"],
            "step_limit": lv["step_limit"],
            "grid": lv["grid"], "targets": lv["targets"],
            "ai_difficulty": lv.get("ai_difficulty", 0),
        })

    candidates = [s for s in scored
                  if s["boxes"] <= 5 and s["bfs_steps"] is not None
                  and s["difficulty"] >= 1]

    by_boxes = defaultdict(list)
    for c in candidates:
        by_boxes[c["boxes"]].append(c)

    print(f"\nStory candidates (≤5 boxes, solvable): {len(candidates)}")
    for b in sorted(by_boxes):
        print(f"  {b} box: {len(by_boxes[b])}")

    wave = build_wave_targets(97)
    box_seq = []
    b_pattern = [1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5]
    for i in range(97):
        box_seq.append(b_pattern[i % len(b_pattern)])

    selected = []
    used = set(str(lv["grid"]) for lv in preserved)

    for i, (target_diff, target_box) in enumerate(zip(wave, box_seq)):
        lid = i + 4

        # Best match: same box count, exact difficulty
        pool = [c for c in by_boxes.get(target_box, [])
                if str(c["grid"]) not in used]
        pool.sort(key=lambda c: abs(c["difficulty"] - target_diff))

        if not pool or abs(pool[0]["difficulty"] - target_diff) > 2:
            # Relax box count, find any nearby difficulty
            pool = [c for c in candidates if str(c["grid"]) not in used]
            pool.sort(key=lambda c: abs(c["difficulty"] - target_diff))
            if pool and abs(pool[0]["difficulty"] - target_diff) <= 2:
                pass
            elif not pool:
                print(f"  WARNING: No candidate for L{lid}")
                continue

        pick = pool[0]
        used.add(str(pick["grid"]))
        selected.append({
            "id": lid,
            "name": f"第{lid:04d}关",
            "cols": pick["cols"], "rows": pick["rows"],
            "step_limit": max(pick["bfs_steps"] * 4 + 5, 30),
            "grid": pick["grid"], "targets": pick["targets"],
            "ai_difficulty": pick["difficulty"],
        })

    return preserved + selected


def select_challenge_levels(scored, used_grids, n=900):
    """Select 900 levels for challenge mode."""
    candidates = [s for s in scored
                  if s["difficulty"] >= 4
                  and s["boxes"] <= 15
                  and str(s["grid"]) not in used_grids]

    # Sort by difficulty (asc), then box count, then BFS steps
    candidates.sort(key=lambda c: (c["difficulty"], c["boxes"],
                                   c["bfs_steps"] or 9999))

    print(f"\nChallenge candidates (diff≥4): {len(candidates)}")

    selected = []
    used = set(used_grids)
    diff_curve = 4.0
    step = (10.0 - 4.0) / n

    last_box = 0
    streak = 0

    for i in range(n):
        target = round(diff_curve)

        pool = [c for c in candidates
                if c["difficulty"] >= target and str(c["grid"]) not in used]
        if streak >= 3:
            pool = [c for c in pool if c["boxes"] != last_box]
        if not pool:
            pool = [c for c in candidates if str(c["grid"]) not in used]
            if not pool:
                print(f"  WARNING: Only {i}/{n} challenge levels!")
                break

        # Gradually prefer larger puzzles as difficulty increases
        ideal_boxes = min(15, max(1, (target - 3) * 3))
        pool.sort(key=lambda c: (abs(c["difficulty"] - target),
                                 abs(c["boxes"] - ideal_boxes) if target >= 6 else c["boxes"],
                                 c.get("bfs_steps") or 9999))
        pick = pool[0]
        used.add(str(pick["grid"]))

        if pick["boxes"] == last_box:
            streak += 1
        else:
            streak = 0
            last_box = pick["boxes"]

        lid = i + 101
        selected.append({
            "id": lid,
            "name": f"挑战关 {lid}",
            "cols": pick["cols"], "rows": pick["rows"],
            "step_limit": max(pick["bfs_steps"] * 3 + 10, 50)
                          if pick["bfs_steps"] else 999,
            "grid": pick["grid"], "targets": pick["targets"],
            "ai_difficulty": pick["difficulty"],
        })
        diff_curve += step

    return selected


# ── Main ──────────────────────────────────────────────────────────────

def main():
    scored = phase1_load_or_score()

    # Load current levels to preserve 1-3
    current = {"levels": []}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            current = json.load(f)
    lv1_3 = [lv for lv in current.get("levels", []) if lv["id"] <= 3]
    if len(lv1_3) < 3:
        print("WARNING: <3 levels in current levels.json. Using fallback.")
        # Keep at most what we have
    print(f"Preserved levels 1-3 from current file: {len(lv1_3)}")

    # Story mode
    print("\n" + "=" * 60)
    print("Phase 2a: Story levels 1-100...")
    print("=" * 60)
    story = select_story_levels(scored, lv1_3)

    used = set(str(lv["grid"]) for lv in story)

    # Challenge mode
    print("\n" + "=" * 60)
    print("Phase 2b: Challenge levels 101-1000...")
    print("=" * 60)
    challenge = select_challenge_levels(scored, used, 900)

    all_levels = sorted(story + challenge, key=lambda x: x["id"])

    # Stats
    print(f"\nTotal: {len(all_levels)} levels")
    diff_dist = defaultdict(int)
    box_dist = defaultdict(int)
    for lv in all_levels:
        diff_dist[int(lv.get("ai_difficulty", 0))] += 1
        box_dist[sum(row.count(2) for row in lv["grid"])] += 1

    print("\nDifficulty distribution:")
    for d in sorted(diff_dist):
        print(f"  {d}: {diff_dist[d]}")

    print("\nBox distribution:")
    for b in sorted(box_dist):
        print(f"  {b}: {box_dist[b]}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"levels": all_levels}, f, indent=2, ensure_ascii=False)
    print(f"\nWritten to {OUTPUT_FILE}")

    # Save metadata-only version (no grids) for fast startup
    meta_levels = []
    for lv in all_levels:
        ml = {k: v for k, v in lv.items() if k != "grid"}
        meta_levels.append(ml)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump({"levels": meta_levels}, f, indent=2, ensure_ascii=False)
    print(f"Written to {META_FILE} ({len(meta_levels)} levels, no grid)")

    # Story wave preview
    print(f"\nStory mode wave (first 20):")
    for lv in story[:20]:
        b = sum(row.count(2) for row in lv["grid"])
        bar = "█" * int(lv.get("ai_difficulty", 0))
        print(f"  L{lv['id']:3d} | {b}箱 | diff={lv['ai_difficulty']} {bar}")

    # Challenge progression
    print(f"\nChallenge progression (sample):")
    for i in range(0, len(challenge), 150):
        lv = challenge[i]
        b = sum(row.count(2) for row in lv["grid"])
        print(f"  L{lv['id']:3d} | {b}箱 | diff={lv['ai_difficulty']}")


if __name__ == "__main__":
    main()
