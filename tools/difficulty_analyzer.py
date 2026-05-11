#!/usr/bin/env python3
"""
难度分析工具：分析社区关卡库的结构特征和BFS求解结果。
"""

import json
import os
import sys
from collections import defaultdict

# 把项目根目录加入路径，方便导入 bfs_solver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.bfs_solver import solve

POOLS_DIR = "data/pools"


def load_levels_from_pools(max_boxes=15):
    """加载所有 <= max_boxes 箱的关卡"""
    all_levels = []
    for i in range(1, max_boxes + 1):
        path = os.path.join(POOLS_DIR, f"pool_{i}box.json")
        if os.path.exists(path):
            data = json.load(open(path))
            if isinstance(data, list):
                for lv in data:
                    lv["box_count"] = i
                    all_levels.append(lv)
            elif isinstance(data, dict):
                for lv in data.get("levels", []):
                    lv["box_count"] = i
                    all_levels.append(lv)
    return all_levels


def analyze_level(lv):
    """分析关卡的结构特征"""
    grid = lv["grid"]
    rows = lv["rows"]
    cols = lv["cols"]

    # 计算空地数
    empty = 0
    walls = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 0 or grid[r][c] == 3:
                empty += 1
            elif grid[r][c] == 1:
                walls += 1

    boxes = lv["box_count"]
    density = boxes / empty if empty > 0 else 1.0

    # 死锁检测：L型墙角
    # 遍历每个墙格，检查是否形成L型死角
    # 如果一个空地格的两个垂直方向都是墙，它就是个角死锁陷阱
    deadlock_cells = 0
    total_interior = 0
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == 0:
                total_interior += 1
                # 检查四个方向的L型墙角
                # 右上角: 右边是墙 + 上边是墙
                if (grid[r][c + 1] == 1 and grid[r - 1][c] == 1):
                    deadlock_cells += 1
                # 右下角: 右边是墙 + 下边是墙
                elif (grid[r][c + 1] == 1 and grid[r + 1][c] == 1):
                    deadlock_cells += 1
                # 左上角: 左边是墙 + 上边是墙
                elif (grid[r][c - 1] == 1 and grid[r - 1][c] == 1):
                    deadlock_cells += 1
                # 左下角: 左边是墙 + 下边是墙
                elif (grid[r][c - 1] == 1 and grid[r + 1][c] == 1):
                    deadlock_cells += 1

    deadlock_density = deadlock_cells / total_interior if total_interior > 0 else 0

    # 跑BFS
    try:
        bfs_steps = solve(lv)
        solvable = bfs_steps > 0
    except Exception as e:
        bfs_steps = -1
        solvable = False

    return {
        "steps": bfs_steps,
        "solvable": solvable,
        "boxes": boxes,
        "cols": cols,
        "rows": rows,
        "cells": rows * cols,
        "empty": empty,
        "walls": walls,
        "density": round(density, 4),
        "deadlock_density": round(deadlock_density, 4),
        "deadlock_cells": deadlock_cells,
    }


def main():
    print("加载社区关卡库...")
    all_levels = load_levels_from_pools(15)
    print(f"  共 {len(all_levels)} 关 (1-15箱)")

    # 只分析 <= 100 格 且 <= 4 箱的
    candidates = [lv for lv in all_levels if lv["rows"] * lv["cols"] <= 100 and lv["box_count"] <= 4]
    print(f"  <=100格且<=4箱: {len(candidates)} 关")

    results = []
    for i, lv in enumerate(candidates):
        if i % 500 == 0:
            print(f"  分析进度: {i}/{len(candidates)}")
        result = analyze_level(lv)
        result["id"] = i
        result["source"] = f"pool_{lv['box_count']}box.json"
        if result["solvable"]:
            results.append(result)

    print(f"\n  BFS可解: {len(results)} 关")
    print(f"  BFS不可解: {len(candidates) - len(results)} 关")

    if not results:
        print("没有可解的关卡！")
        return

    # 按步数分组统计
    print("\n  BFS步数分布:")
    ranges = [(0, 5), (6, 10), (11, 15), (16, 20), (21, 30), (31, 50), (51, 100), (100, 999)]
    for lo, hi in ranges:
        count = sum(1 for r in results if lo < r["steps"] <= hi)
        if count > 0:
            print(f"    {lo+1}-{hi}步: {count}关")

    # 保存完整分析结果
    output = {
        "total_analyzed": len(results),
        "levels": sorted(results, key=lambda x: x["steps"])
    }
    json.dump(output, open("data/pools/analysis_results.json", "w"), indent=2)
    print(f"\n  完整分析已保存到 data/pools/analysis_results.json")


if __name__ == "__main__":
    main()
