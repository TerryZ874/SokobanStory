#!/usr/bin/env python3
"""
1. 分析社区库关卡的结构特征 + BFS求解
2. 按波形曲线挑选17关替换 levels.json 的 4-20关
3. 输出新的 levels.json
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.bfs_solver import solve

POOLS_DIR = "data/pools/small"

# ========== 1. 加载并分析社区关卡 ==========
print("=== 阶段1: 加载并分析社区关卡 ===")

all_levels = []  # 每个元素: {boxes, raw:原始关卡数据, steps, density, deadlock_density, cols, rows}
for i in range(1, 5):  # 1-4箱
    path = os.path.join(POOLS_DIR, f"pool_{i}box.json")
    if not os.path.exists(path):
        continue
    data = json.load(open(path))
    levels = data if isinstance(data, list) else data.get("levels", [])
    print(f"  pool_{i}box.json: {len(levels)}关")
    for idx, lv in enumerate(levels):
        grid = lv["grid"]
        rows = len(grid)
        cols = len(grid[0])
        if rows * cols > 100:
            continue

        # 结构分析
        empty = sum(row.count(0) + row.count(3) for row in grid)
        walls = sum(row.count(1) for row in grid)
        density = i / empty if empty > 0 else 1.0

        # 死锁分析
        deadlock_cells = 0
        interior = 0
        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                if grid[r][c] == 0:
                    interior += 1
                    # L型墙角
                    if (grid[r][c+1]==1 and grid[r-1][c]==1) or \
                       (grid[r][c+1]==1 and grid[r+1][c]==1) or \
                       (grid[r][c-1]==1 and grid[r-1][c]==1) or \
                       (grid[r][c-1]==1 and grid[r+1][c]==1):
                        deadlock_cells += 1

        deadlock_density = deadlock_cells / interior if interior > 0 else 0

        # BFS
        try:
            steps = solve(lv)
        except:
            steps = -1

        if steps > 0:
            all_levels.append({
                "boxes": i,
                "pool_idx": idx,
                "raw": lv,
                "steps": steps,
                "density": density,
                "deadlock_density": deadlock_density,
                "cols": cols,
                "rows": rows,
                "cells": rows * cols,
            })

print(f"\n  总可解关卡(≤100格, ≤4箱): {len(all_levels)}关")

# 分布统计
by_boxes = {}
for lv in all_levels:
    by_boxes.setdefault(lv["boxes"], []).append(lv)
for b in sorted(by_boxes.keys()):
    print(f"  {b}箱: {len(by_boxes[b])}关 "
          f"(BFS范围 {min(l['steps'] for l in by_boxes[b])}-{max(l['steps'] for l in by_boxes[b])}步)")

# ========== 2. 按波形曲线挑选 ==========
print("\n=== 阶段2: 波形曲线挑选 ===")

def find_candidates(boxes, lo, hi, used_pool_indices):
    """找候选关卡"""
    candidates = [lv for lv in by_boxes.get(boxes, [])
                  if lo <= lv["steps"] <= hi
                  and lv["pool_idx"] not in used_pool_indices]
    return candidates

def sort_key(pref):
    sorts = {
        "low_density": lambda x: x["density"],
        "high_density": lambda x: -x["density"],
        "low_deadlock": lambda x: x["deadlock_density"],
        "high_deadlock": lambda x: -x["deadlock_density"],
        "medium_deadlock": lambda x: abs(x["deadlock_density"] - 0.18),
        "small_board": lambda x: x["cols"] * x["rows"],
        "large_board": lambda x: -x["cols"] * x["rows"],
    }
    return sorts.get(pref, lambda x: x["steps"])

targets = [
    (4,  2, (5, 9),    10, "low_density",     "第四关：初探双箱"),
    (5,  2, (10, 14),   8, "high_density",    "第五关：双箱迷阵"),
    (6,  3, (5, 9),    10, "small_board",     "第六关：三箱起手"),
    (7,  3, (12, 18),   7, "low_density",     "第七关：三箱探索"),
    (8,  3, (9, 13),    8, "high_density",    "第八关：三箱夹击"),
    (9,  3, (16, 22),   7, "medium_deadlock", "第九关：三箱迂回"),
    (10, 3, (22, 28),   6, "high_deadlock",   "第十关：三箱绝境"),
    (11, 4, (14, 20),   7, "small_board",     "第十一关：四箱初现"),
    (12, 4, (22, 28),   6, "high_deadlock",   "第十二关：四箱困局"),
    (13, 4, (18, 23),   7, "large_board",     "第十三关：四箱迷宫"),
    (14, 4, (27, 33),   5, "high_density",    "第十四关：四箱推演"),
    (15, 4, (22, 27),   6, "low_deadlock",    "第十五关：四箱舒展"),
    (16, 4, (30, 37),   5, "high_deadlock",   "第十六关：四箱风暴"),
    (17, 4, (26, 31),   5, "large_board",     "第十七关：四箱深渊"),
    (18, 4, (33, 39),   4, "high_density",    "第十八关：四箱炼狱"),
    (19, 4, (28, 34),   5, "medium_deadlock", "第十九关：黎明之前"),
    (20, 4, (45, 65),   3, "high_deadlock",   "第二十关：终局之战"),
]

selected = {}
used_pool_indices = {1: set(), 2: set(), 3: set(), 4: set()}

print(f"{'关':>3} {'名称':<16} {'箱':>2} {'BFS':>4} {'步限':>4} {'松紧':>4} {'死锁':>6} {'密度':>5} {'棋盘':>6}")
print("-" * 68)

for lid, boxes, (lo, hi), ratio, pref, name in targets:
    pool = find_candidates(boxes, lo, hi, used_pool_indices[boxes])
    if not pool:
        print(f"  {lid:3d} {name:<16} — 无候选! (放宽范围)")
        # 放宽范围 ±10步
        pool = find_candidates(boxes, lo-10, hi+10, used_pool_indices[boxes])
        if not pool:
            # 再放宽
            pool = find_candidates(boxes, 1, 200, used_pool_indices[boxes])

    pool.sort(key=sort_key(pref))
    picked = pool[0]
    used_pool_indices[boxes].add(picked["pool_idx"])

    step_limit = max(ratio * picked["steps"], picked["steps"] + 15)
    step_limit = min(step_limit, 300)

    selected[lid] = picked
    picked["new_step_limit"] = int(step_limit)
    picked["new_name"] = name

    print(f"  {lid:3d} {name:<16} {boxes:2d}箱 {picked['steps']:3d}步 "
          f"{int(step_limit):3d} {step_limit/picked['steps']:4.1f}x "
          f"{picked['deadlock_density']:.2f} {picked['density']:.2f} "
          f"{picked['cols']}x{picked['rows']}")

# 波形曲线
print("\n波形曲线:")
steps_list = [selected[lid]["steps"] for lid in sorted(selected.keys())]
for i, s in enumerate(steps_list, 4):
    bar = "█" * (s // 3) if s > 0 else ""
    print(f"  {i:2d} ({s:2d}步) {bar}")

if len(steps_list) >= 2:
    ratio_20_19 = steps_list[-1] / steps_list[-2] if steps_list[-2] > 0 else 0
    print(f"\n第20关 BFS={steps_list[-1]}步 — 是第19关({steps_list[-2]}步)的 {ratio_20_19:.1f}倍")

# ========== 3. 生成新的 levels.json ==========
print("\n=== 阶段3: 生成新的 levels.json ===")

# 保留前3关
current = json.load(open("data/levels.json"))
new_levels = current["levels"][:3]  # 只保留1-3关

errors = []
for lid in sorted(selected.keys()):
    pick = selected[lid]
    raw = pick["raw"]
    grid = raw["grid"]
    targets_coords = raw.get("targets", raw.get("Targets", []))

    # 如果没有targets字段，从grid推算
    if not targets_coords:
        targets_coords = []
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == 4:  # 已到目标的箱子
                    targets_coords.append([c, r])
                    grid[r][c] = 2  # 转为普通箱子
                # 找目标点标记（可能有单独的target标记）
        if not targets_coords:
            errors.append(f"第{lid}关无目标点")
            continue

    new_lv = {
        "id": lid,
        "name": pick["new_name"],
        "cols": pick["cols"],
        "rows": pick["rows"],
        "step_limit": pick["new_step_limit"],
        "grid": grid,
        "targets": targets_coords,
    }

    # 验证可解
    try:
        bfs_check = solve(new_lv)
        if bfs_check <= 0:
            errors.append(f"第{lid}关 BFS验证失败!")
            continue
    except:
        errors.append(f"第{lid}关 BFS异常!")
        continue

    new_levels.append(new_lv)

print(f"  成功构建: {len(new_levels)}关")
if errors:
    print(f"  错误: {errors}")

if len(new_levels) == 20:
    output = {"levels": new_levels}
    json.dump(output, open("data/levels.json", "w"), indent=2)
    print("  ✅ levels.json 已更新!")
else:
    print(f"  ❌ 只构建了{len(new_levels)}关，未保存")

# 输出最终难度曲线
print("\n最终难度曲线:")
print(f"{'ID':>3} {'名称':<16} {'BFS':>4} {'步限':>4} {'松紧':>4}")
for lv in new_levels:
    steps = steps_list[lv["id"] - 4] if lv["id"] >= 4 else "-"
    if isinstance(steps, int):
        print(f"  {lv['id']:3d} {lv['name']:<16} {steps:4d}步 {lv['step_limit']:4d} {lv['step_limit']/steps:4.1f}x")
    else:
        print(f"  {lv['id']:3d} {lv['name']:<16}   -   {lv['step_limit']:4d} (保留原关)")
