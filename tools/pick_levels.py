#!/usr/bin/env python3
"""
从社区关卡库中挑选17关替换主线4-20关。
波形曲线 + 避免重复 + 输出可直接替换 levels.json 的数据。
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.bfs_solver import solve

# 加载分析结果
analysis = json.load(open("data/pools/analysis_results.json"))
analysis_by_id = {lv["id"]: lv for lv in analysis["levels"]}

POOLS_DIR = "data/pools/small"
def load_raw_pools():
    """加载关卡池原始数据，并关联分析结果"""
    all_raw = []
    for i in range(1, 5):  # 1-4箱
        path = f"{POOLS_DIR}/pool_{i}box.json"
        if os.path.exists(path):
            raw_data = json.load(open(path))
            if isinstance(raw_data, list):
                for idx, lv in enumerate(raw_data):
                    lv["_boxes"] = i
                    lv["_pool_idx"] = idx
                    all_raw.append(lv)
    return all_raw

raw_levels = load_raw_pools()

# 按箱子数分组
by_boxes = {}
for lv in analysis["levels"]:
    by_boxes.setdefault(lv["boxes"], []).append(lv)


def find_candidates(boxes, min_steps, max_steps, used_ids):
    pool = [lv for lv in by_boxes.get(boxes, [])
            if min_steps <= lv["steps"] <= max_steps
            and lv["id"] not in used_ids]
    return pool


def pref_sort(pref):
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


def find_raw_level(analysis_lv):
    """根据分析结果找到原始关卡数据"""
    for rl in raw_levels:
        if (rl["_boxes"] == analysis_lv["boxes"] and
            rl.get("cols", rl.get("Cols", 0)) == analysis_lv["cols"] and
            rl.get("rows", rl.get("Rows", 0)) == analysis_lv["rows"]):
            # 验证grid是否匹配
            grid_a = str(analysis_lv.get("grid", ""))
            grid_b = str(rl.get("grid", rl.get("Grid", "")))
            if grid_a[:50] == grid_b[:50]:  # 粗略匹配
                return rl
    return None


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
used_ids = set()

print("挑选结果:")
print(f"{'ID':>3} {'名称':<14} {'箱':>2} {'BFS':>4} {'步限':>4} {'松紧':>4} {'死锁密度':>8} {'密度':>6} {'尺寸':>6}")
print("-" * 65)

for level_id, boxes, (lo, hi), ratio, pref, name in targets:
    pool = find_candidates(boxes, lo, hi, used_ids)
    if not pool:
        print(f"  {level_id:3d}: 无候选!")
        continue

    pool.sort(key=pref_sort(pref))
    picked = pool[0]
    used_ids.add(picked["id"])

    step_limit = max(ratio * picked["steps"], picked["steps"] + 20)
    step_limit = min(step_limit, 300)

    selected[level_id] = {
        "analysis": picked,
        "step_limit": step_limit,
        "name": name,
    }

    print(f"  {level_id:3d} {name:<14} {boxes:2d}箱 {picked['steps']:3d}步 "
          f"{step_limit:3d} {step_limit/picked['steps']:4.1f}x "
          f"{picked['deadlock_density']:7.2f} {picked['density']:5.2f} "
          f"{picked['cols']}x{picked['rows']}")

# 波形曲线
print("\n波形曲线:")
steps_list = [selected[lid]["analysis"]["steps"] for lid in sorted(selected.keys())]
for i, s in enumerate(steps_list, 4):
    bar = "█" * (s // 3)
    print(f"  {i:2d} ({s:2d}步) {bar}")

print(f"\n第20关 BFS={steps_list[-1]}步 — 是第19关({steps_list[-2]}步)的 "
      f"{steps_list[-1]/steps_list[-2]:.1f}倍")

# 输出JSON替换数据
print("\n\n替换数据 (可直接写入 levels.json 的 levels[3:] 部分):")
print("=" * 60)

# 需要读取原始pool文件找到完整的grid数据
def get_original_level(boxes, pool_index):
    """从原始pool文件读取关卡数据"""
    path = f"{POOLS_DIR}/pool_{boxes}box.json"
    raw = json.load(open(path))
    if isinstance(raw, list):
        return raw[pool_index]
    return None

# 但是分析结果中没有pool_index... 我们需要重新匹配
# 简化方案：直接从raw_levels中通过分析id找到对应的原始关卡
analysis_id_to_raw = {}
# 先给raw_levels也跑一下BFS来对齐... 或者换个方式
# 实际上我们只需要分析结果中的"id"这个索引，对应到原始pool_*box.json中的索引

# 更好的方式：重新读取pool文件，找到索引位置
for i in range(1, 5):
    path = f"{POOLS_DIR}/pool_{i}box.json"
    if os.path.exists(path):
        raw_data = json.load(open(path))
        if isinstance(raw_data, list):
            for idx, lv in enumerate(raw_data):
                # 在analysis_by_id中查找
                for aid, alv in analysis_by_id.items():
                    if (alv["boxes"] == i and
                        alv["cols"] == len(lv.get("grid", lv.get("Grid", []))[0]) if isinstance(lv.get("grid", lv.get("Grid", [])), list) and len(lv.get("grid", lv.get("Grid", []))) > 0 else False and
                        alv["rows"] == len(lv.get("grid", lv.get("Grid", []))) if isinstance(lv.get("grid", lv.get("Grid", [])), list) else False):
                        # 找到了，保存映射
                        analysis_id_to_raw[aid] = {"boxes": i, "pool_idx": idx, "day_raw": lv}
                        break

# 简化处理：直接从原始pool文件通过索引读取
# 实际analysis levels按id递增顺序对应pool文件顺序
analysis_sorted = sorted(analysis["levels"], key=lambda x: x["id"])
box_start_indices = {}
for i in range(1, 5):
    # 找到每个箱子数的起始analysis id
    box_levels = [lv for lv in analysis_sorted if lv["boxes"] == i]
    if box_levels:
        box_start_indices[i] = box_levels[0]["id"]

print(f"\n箱子起始索引: {box_start_indices}")
print(f"\n总共选了 {len(selected)} 关")

# 保存选择结果
output = {
    "selected": {},
    "curve": [selected[lid]["analysis"]["steps"] for lid in sorted(selected.keys())]
}
for lid, s in selected.items():
    output["selected"][lid] = {
        "analysis_id": s["analysis"]["id"],
        "boxes": s["analysis"]["boxes"],
        "bfs_steps": s["analysis"]["steps"],
        "step_limit": s["step_limit"],
        "name": s["name"],
        "cols": s["analysis"]["cols"],
        "rows": s["analysis"]["rows"],
        "density": s["analysis"]["density"],
        "deadlock_density": s["analysis"]["deadlock_density"],
    }

json.dump(output, open("data/pools/selected_levels.json", "w"), indent=2)
print("选择结果已保存到 data/pools/selected_levels.json")
