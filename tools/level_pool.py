#!/usr/bin/env python3
"""
Level Pool Builder — 按箱子数分类社区关卡库。

流程:
  1. 扫描 reference/38168/ 全部关卡文件
  2. 解析每个关卡，提取元数据（箱子数、尺寸、来源）
  3. 小关卡（≤4箱, ≤100格）运行 BFS 验证
  4. 按箱子数分组，写入 data/pools/pool_Nbox.json
  5. 生成统计报告 data/pools/README.md

用法:
  python3 tools/level_pool.py
  python3 tools/level_pool.py --skip-bfs   # 跳过 BFS（快速分类）
"""

import json
import os
import re
import sys
import time

SRC_DIR = "reference/38168"
OUT_DIR = "data/pools"
BFS_MAX_BOXES = 4
BFS_MAX_CELLS = 100

from typing import Optional, List

CHAR_MAP = {
    '#': 1, '-': 0, ' ': 0, '.': 0,
    '$': 2, '@': 3, '*': 2, '+': 3,
}


def parse_one(block: str, src_name: str, level_num: int) -> Optional[dict]:
    """Parse a single SLC block into a level dict."""
    lines = [l for l in block.split('\n') if '#' in l]
    if not lines:
        return None
    max_w = max(len(l) for l in lines)
    lines = [l.ljust(max_w) for l in lines]

    grid, targets = [], []
    for y, line in enumerate(lines):
        row = []
        for x, ch in enumerate(line):
            if ch in ('.', '*', '+'):
                targets.append([x, y])
            if ch in ('$', '*'):
                row.append(2)
            elif ch in ('@', '+'):
                row.append(3)
            elif ch == '#':
                row.append(1)
            else:
                row.append(0)
        grid.append(row)

    pc = sum(r.count(3) for r in grid)
    bc = sum(r.count(2) for r in grid)
    if pc != 1 or bc == 0 or len(targets) != bc:
        return None

    m = re.search(r'Title:(.+)', block)
    title = m.group(1).strip() if m else f"#{level_num}"
    a = re.search(r'Author:(.+)', block)
    author = a.group(1).strip() if a else "Unknown"

    return {
        "source": src_name,
        "num": level_num,
        "title": title,
        "author": author,
        "cols": len(grid[0]),
        "rows": len(grid),
        "boxes": bc,
        "cells": len(grid[0]) * len(grid),
        "step_limit": max(bc * 40, 20),
        "grid": grid,
        "targets": targets,
    }


def load_file(fpath: str) -> Optional[str]:
    for enc in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
        try:
            with open(fpath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return None


def get_blocks(content: str) -> List[str]:
    blocks = re.split(r'\n\s*\n', content)
    return [b.strip() for b in blocks if b.strip() and '#' in b]


# ── BFS solver (minimal, copied from bfs_solver.py) ──

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


def bfs_solve(level: dict) -> Optional[int]:
    """Returns min steps or None (unsolvable / too complex)."""
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

    dead_positions = _deadlocks(walls, target_set, cols, rows)

    from collections import deque
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
                if (bx, by) not in target_set and (bx, by) in dead_positions:
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


# ── Main ──

def main():
    skip_bfs = "--skip-bfs" in sys.argv

    if not os.path.isdir(SRC_DIR):
        print(f"Error: {SRC_DIR} not found. Run from project root.")
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)

    files = sorted(os.listdir(SRC_DIR))
    all_levels = []
    total_parsed = 0
    total_errors = 0

    print("Parsing level files...")
    for fname in files:
        if not fname.lower().endswith(('.txt', '.sok', '.slc', '.xsb')):
            continue
        fpath = os.path.join(SRC_DIR, fname)
        content = load_file(fpath)
        if content is None:
            print(f"  WARN: Cannot decode {fname}")
            total_errors += 1
            continue
        blocks = get_blocks(content)
        src_name = os.path.splitext(fname)[0]
        for i, block in enumerate(blocks):
            lv = parse_one(block, src_name, i + 1)
            if lv:
                all_levels.append(lv)
                total_parsed += 1
            else:
                total_errors += 1

    print(f"\nParsed {total_parsed} levels, {total_errors} errors\n")

    # Group by box count
    pools: dict[int, list] = {}
    for lv in all_levels:
        bc = lv['boxes']
        pools.setdefault(bc, []).append(lv)

    # BFS on small levels
    if not skip_bfs:
        print("--- BFS Verification (≤{} boxes, ≤{} cells) ---".format(BFS_MAX_BOXES, BFS_MAX_CELLS))
        bfs_ok = 0
        bfs_fail = 0
        bfs_skip = 0

        for bc in sorted(pools.keys()):
            if bc > BFS_MAX_BOXES:
                bfs_skip += len(pools[bc])
                continue
            for lv in pools[bc]:
                if lv['cells'] > BFS_MAX_CELLS:
                    lv['bfs'] = None
                    bfs_skip += 1
                    continue
                steps = bfs_solve(lv)
                if steps is not None:
                    lv['bfs'] = steps
                    bfs_ok += 1
                else:
                    lv['bfs'] = None
                    bfs_fail += 1

            print(f"  {bc} boxes: done")

        print(f"\nBFS results: {bfs_ok} solvable, {bfs_fail} unsolvable, {bfs_skip} skipped (too complex)")
    else:
        for lv in all_levels:
            lv['bfs'] = None

    # Write pool files
    print("\n--- Writing pool files ---")
    total_written = 0
    for bc in sorted(pools.keys()):
        entries = pools[bc]
        # Strip grid/targets from output? No, keep them — we need them for game loading
        # But let's also include a "light" version without grid data for stats
        data = {
            "box_count": bc,
            "total": len(entries),
            "levels": entries,
        }
        fname = f"pool_{bc}box.json"
        # For 0-box and very large pools, skip writing (no valid levels with 0 boxes)
        if bc == 0:
            continue
        fpath = os.path.join(OUT_DIR, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        total_written += len(entries)
        bf = sum(1 for e in entries if e.get('bfs') is not None)
        sz = os.path.getsize(fpath)
        print(f"  {fname}: {len(entries):5d} levels ({bf:3d} BFS-verified) {sz//1024}KB")

    # Write summary metadata (lightweight JSON without grid data)
    summary = {}
    for bc in sorted(pools.keys()):
        if bc == 0:
            continue
        entries = pools[bc]
        bf = [e for e in entries if e.get('bfs') is not None]
        summary[str(bc)] = {
            "total": len(entries),
            "bfs_verified": len(bf),
            "bfs_solvable": sum(1 for e in bf if e['bfs'] is not None),
            "bfs_unsolvable": sum(1 for e in bf if e['bfs'] is None),
            "col_range": [min(e['cols'] for e in entries), max(e['cols'] for e in entries)],
            "row_range": [min(e['rows'] for e in entries), max(e['rows'] for e in entries)],
        }

    with open(os.path.join(OUT_DIR, "_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)

    # Generate README.md
    gen_report(pools, summary, total_parsed)

    print(f"\n✅ Done. {total_written} levels written to {OUT_DIR}/")


def gen_report(pools, summary, total):
    lines = [
        "# 社区关卡库覆盖面统计\n",
        f"**来源**: `reference/38168/` ({len(os.listdir(SRC_DIR))} 个文件)",
        f"**总关卡数**: {total}\n",
        "## 按箱子数分布\n",
        "| 箱子数 | 关卡数 | BFS 验证 | 可解 | 不可解 | 列范围 | 行范围 |",
        "|--------|-------:|---------:|-----:|------:|------:|------:|",
    ]

    for bc in sorted(pools.keys()):
        if bc == 0:
            continue
        s = summary.get(str(bc), {})
        lines.append(
            f"| {bc}箱 | {s.get('total',0):,} | {s.get('bfs_verified',0):,} "
            f"| {s.get('bfs_solvable', 0):,} | {s.get('bfs_unsolvable', 0):,} "
            f"| {s.get('col_range',[0,0])[0]}–{s.get('col_range',[0,0])[1]} "
            f"| {s.get('row_range',[0,0])[0]}–{s.get('row_range',[0,0])[1]} |"
        )

    lines += [
        "\n## 文件说明\n",
        "| 文件 | 内容 |",
        "|------|------|",
    ]
    for bc in sorted(pools.keys()):
        if bc == 0:
            continue
        lines.append(f"| `pool_{bc}box.json` | {bc}箱关卡 ({pools[bc][0]['cells']}–{pools[bc][-1]['cells']} 格) |")

    lines += [
        "\n## 用法\n",
        "加载特定箱子数的关卡池：",
        "```python\nimport json\n",
        'pool = json.load(open(f"data/pools/pool_3box.json"))\n',
        'for level in pool["levels"]:\n    print(level["title"], level["bfs"], "steps")\n',
        "```\n",
    ]

    with open(os.path.join(OUT_DIR, "README.md"), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"  README.md written")


if __name__ == '__main__':
    t0 = time.time()
    main()
    print(f"Elapsed: {time.time() - t0:.0f}s")
