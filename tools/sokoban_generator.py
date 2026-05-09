#!/usr/bin/env python3
"""
Sokoban 关卡生成器 — 逆向拉动法

方法论（对应 GDD/sokoban_level_generate.md）:
1. 根据每关剧情的压抑感 (oppression) 和复杂度 (complexity) 设计墙布局
2. 箱子从目标点开始，逆向拉动到起始位置
3. BFS 求解器验证可解性和难度评分
4. 选择最符合剧情参数的关卡配置

输出: data/levels.json
"""

import json
import random
import sys
from collections import deque
from copy import deepcopy

# ── 常量 ──────────────────────────────────────────────
FLOOR = 0
WALL  = 1
BOX   = 2
PLAYER = 3

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # ↑ ↓ ← →

# ── 辅助函数 ──────────────────────────────────────────

def in_bounds(x, y, cols, rows):
    return 0 <= x < cols and 0 <= y < rows

def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def add_pos(p, d):
    return (p[0] + d[0], p[1] + d[1])

# ── 基本墙布局模板 ────────────────────────────────────
# 每个模板定义: cols, rows, walls (1的坐标), targets
# 压抑感越高: 墙越多, 走廊越窄, 房间越小

TEMPLATES = []

def _add_template(t):
    TEMPLATES.append(t)

# ── Level 1: 初识推箱 ── oppression=0.10, complexity=0.10 ──
_add_template({
    "id": 1, "name": "第一关：初识推箱",
    "cols": 5, "rows": 4, "step_limit": 8,
    "oppression": 0.10, "complexity": 0.10,
    "walls": [
    ],
    "targets": [(3, 2)],
    "num_pulls": 1,
    "num_boxes": 1,
})

# ── Level 2: U 形弯 ── oppression=0.15, complexity=0.15 ──
_add_template({
    "id": 2, "name": "第二关：U 形弯",
    "cols": 6, "rows": 5, "step_limit": 12,
    "oppression": 0.15, "complexity": 0.15,
    "walls": [
        # 加一个中央柱
        (2, 1), (2, 2), (2, 3),
    ],
    "targets": [(4, 2)],
    "num_pulls": 2,
    "num_boxes": 1,
})

# ── Level 3: 双箱协作 ── oppression=0.20, complexity=0.20 ──
_add_template({
    "id": 3, "name": "第三关：双箱协作",
    "cols": 6, "rows": 6, "step_limit": 20,
    "oppression": 0.20, "complexity": 0.20,
    "walls": [
        (2, 1), (3, 1),
        (2, 4), (3, 4),
    ],
    "targets": [(2, 2), (4, 4)],
    "num_pulls": 3,
    "num_boxes": 2,
})

# ── Level 4: 转角遇到箱 ── oppression=0.25, complexity=0.30 ──
_add_template({
    "id": 4, "name": "第四关：转角遇到箱",
    "cols": 7, "rows": 5, "step_limit": 15,
    "oppression": 0.25, "complexity": 0.30,
    "walls": [
        (3, 1), (3, 2), (3, 3),
    ],
    "targets": [(5, 2)],
    "num_pulls": 4,
    "num_boxes": 1,
})

# ── Level 5: 一推到底 ── oppression=0.30, complexity=0.35 ──
_add_template({
    "id": 5, "name": "第五关：一推到底",
    "cols": 8, "rows": 5, "step_limit": 20,
    "oppression": 0.30, "complexity": 0.35,
    "walls": [
        (2, 1), (2, 2), (2, 3),
        (5, 1), (5, 2), (5, 3),
    ],
    "targets": [(6, 3)],
    "num_pulls": 4,
    "num_boxes": 1,
})

# ── Level 6: 双箱上推 ── oppression=0.35, complexity=0.40 ──
_add_template({
    "id": 6, "name": "第六关：双箱上推",
    "cols": 8, "rows": 7, "step_limit": 30,
    "oppression": 0.35, "complexity": 0.40,
    "walls": [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
        (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
        (3, 3), (4, 3), (5, 3),
    ],
    "targets": [(3, 2), (4, 5)],
    "num_pulls": 6,
    "num_boxes": 2,
})

# ── Level 7: 向右看齐 ── oppression=0.40, complexity=0.40 ──
_add_template({
    "id": 7, "name": "第七关：向右看齐",
    "cols": 8, "rows": 6, "step_limit": 25,
    "oppression": 0.40, "complexity": 0.40,
    "walls": [
        (3, 1), (3, 2), (3, 3), (3, 4),
        (6, 1), (6, 2), (6, 3), (6, 4),
    ],
    "targets": [(5, 2), (5, 4)],
    "num_pulls": 5,
    "num_boxes": 2,
})

# ── Level 8: T形路 ── oppression=0.45, complexity=0.45 ──
_add_template({
    "id": 8, "name": "第八关：T 形路",
    "cols": 8, "rows": 7, "step_limit": 30,
    "oppression": 0.45, "complexity": 0.45,
    "walls": [
        (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3),
        (3, 1), (4, 5),
    ],
    "targets": [(3, 2), (5, 5)],
    "num_pulls": 7,
    "num_boxes": 2,
})

# ── Level 9: 迂回 ── oppression=0.50, complexity=0.50 ──
_add_template({
    "id": 9, "name": "第九关：迂回",
    "cols": 9, "rows": 7, "step_limit": 35,
    "oppression": 0.50, "complexity": 0.50,
    "walls": [
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
        (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
        (4, 1),
    ],
    "targets": [(4, 2), (5, 5)],
    "num_pulls": 7,
    "num_boxes": 2,
})

# ── Level 10: 三角阵 ── oppression=0.55, complexity=0.55 ──
_add_template({
    "id": 10, "name": "第十关：三角阵",
    "cols": 9, "rows": 8, "step_limit": 40,
    "oppression": 0.55, "complexity": 0.55,
    "walls": [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
        (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6),
        (3, 1), (5, 6),
        (4, 3), (4, 4),
    ],
    "targets": [(3, 3), (5, 3), (4, 5)],
    "num_pulls": 7,
    "num_boxes": 3,
})

# ── Level 11: 通道 ── oppression=0.50, complexity=0.50 ──
_add_template({
    "id": 11, "name": "第十一关：通道",
    "cols": 8, "rows": 7, "step_limit": 30,
    "oppression": 0.50, "complexity": 0.50,
    "walls": [
        (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 5),
    ],
    "targets": [(4, 2), (3, 5)],
    "num_pulls": 6,
    "num_boxes": 2,
})

# ── Level 12: 三足鼎立 ── oppression=0.45, complexity=0.50 ──
_add_template({
    "id": 12, "name": "第十二关：三足鼎立",
    "cols": 9, "rows": 8, "step_limit": 38,
    "oppression": 0.45, "complexity": 0.50,
    "walls": [
        (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6),
        (1, 4), (2, 4),
        (5, 1), (5, 2), (5, 3),
    ],
    "targets": [(5, 4), (6, 6), (4, 6)],
    "num_pulls": 7,
    "num_boxes": 3,
})

# ── Level 13: 竞技场 ── oppression=0.40, complexity=0.55 ──
_add_template({
    "id": 13, "name": "第十三关：竞技场",
    "cols": 9, "rows": 9, "step_limit": 35,
    "oppression": 0.40, "complexity": 0.55,
    "walls": [
        (2, 1), (2, 2), (2, 4), (2, 5), (2, 6), (2, 7),
        (6, 1), (6, 2), (6, 4), (6, 5), (6, 6), (6, 7),
        (4, 3), (4, 4), (4, 5),
    ],
    "targets": [(4, 2), (5, 6), (5, 4)],
    "num_pulls": 7,
    "num_boxes": 3,
})

# ── Level 14: 多段推进 ── oppression=0.50, complexity=0.55 ──
_add_template({
    "id": 14, "name": "第十四关：多段推进",
    "cols": 10, "rows": 9, "step_limit": 40,
    "oppression": 0.50, "complexity": 0.55,
    "walls": [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7),
        (2, 6), (3, 6), (4, 6),
        (6, 2), (6, 3), (7, 2),
    ],
    "targets": [(3, 2), (6, 5), (5, 4)],
    "num_pulls": 8,
    "num_boxes": 3,
})

# ── Level 15: 四箱入门 ── oppression=0.55, complexity=0.60 ──
_add_template({
    "id": 15, "name": "第十五关：四箱入门",
    "cols": 10, "rows": 9, "step_limit": 45,
    "oppression": 0.55, "complexity": 0.60,
    "walls": [
        (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
        (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7),
        (4, 1), (5, 7),
        (4, 4), (5, 4),
    ],
    "targets": [(4, 2), (5, 3), (4, 6), (5, 5)],
    "num_pulls": 8,
    "num_boxes": 4,
})

# ── Level 16: 算力激增 ── oppression=0.60, complexity=0.60 ──
_add_template({
    "id": 16, "name": "第十六关：算力激增",
    "cols": 10, "rows": 9, "step_limit": 45,
    "oppression": 0.60, "complexity": 0.60,
    "walls": [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (3, 3), (3, 4), (3, 5), (3, 6),
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
        (7, 3), (7, 4), (7, 5), (7, 6),
        (8, 1), (8, 7),
    ],
    "targets": [(2, 2), (4, 5), (6, 2), (6, 6)],
    "num_pulls": 8,
    "num_boxes": 4,
})

# ── Level 17: 四面出击 ── oppression=0.65, complexity=0.65 ──
_add_template({
    "id": 17, "name": "第十七关：四面出击",
    "cols": 10, "rows": 9, "step_limit": 48,
    "oppression": 0.65, "complexity": 0.65,
    "walls": [
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
        (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7),
        (4, 1), (4, 2), (4, 3),
        (5, 5), (5, 6), (5, 7),
    ],
    "targets": [(4, 4), (6, 4), (4, 6), (6, 2)],
    "num_pulls": 9,
    "num_boxes": 4,
})

# ── Level 18: 算力风暴 ── oppression=0.70, complexity=0.70 ──
_add_template({
    "id": 18, "name": "第十八关：算力风暴",
    "cols": 10, "rows": 9, "step_limit": 50,
    "oppression": 0.70, "complexity": 0.70,
    "walls": [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (3, 2), (3, 3), (3, 4), (3, 5), (3, 6),
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
        (7, 2), (7, 3), (7, 4), (7, 5), (7, 6),
        (8, 1), (8, 7),
    ],
    "targets": [(2, 2), (4, 3), (6, 4), (4, 6)],
    "num_pulls": 9,
    "num_boxes": 4,
})

# ── Level 19: 黎明之前 ── oppression=0.75, complexity=0.70 ──
_add_template({
    "id": 19, "name": "第十九关：黎明之前",
    "cols": 10, "rows": 9, "step_limit": 52,
    "oppression": 0.75, "complexity": 0.70,
    "walls": [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (3, 1), (3, 2), (3, 3),
        (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
        (7, 1), (7, 2), (7, 3),
        (8, 5), (8, 6), (8, 7),
        (4, 7),
    ],
    "targets": [(2, 4), (4, 2), (6, 4), (4, 6)],
    "num_pulls": 10,
    "num_boxes": 4,
})

# ── Level 20: 终局之战 ── oppression=0.80, complexity=0.75 ──
_add_template({
    "id": 20, "name": "第二十关：终局之战",
    "cols": 10, "rows": 10, "step_limit": 55,
    "oppression": 0.80, "complexity": 0.75,
    "walls": [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
        (3, 2), (3, 3), (3, 4), (3, 6), (3, 7), (3, 8),
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8),
        (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7), (7, 8),
        (8, 1),
        (2, 8), (4, 8), (6, 8),
    ],
    "targets": [(2, 2), (4, 4), (6, 4), (4, 6)],
    "num_pulls": 10,
    "num_boxes": 4,
})


# ── BFS 求解器 ──────────────────────────────────────────

def bfs_solve(grid, cols, rows, targets, player_start, boxes_start):
    """
    BFS 求最短路径。
    返回 (steps, visited_count) 或 (None, visited_count) 不可解。
    """
    target_set = set((t[0], t[1]) for t in targets)
    boxes_start = sorted(boxes_start)
    start = (player_start, tuple(boxes_start))

    # 预计算墙
    walls = set()
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == WALL:
                walls.add((x, y))

    q = deque()
    q.append((start, 0))
    visited = {start}

    while q:
        (player_pos, boxes), steps = q.popleft()
        px, py = player_pos
        boxes = list(boxes)

        # 胜利
        if all(b in target_set for b in boxes):
            return steps, len(visited)

        box_set = set(boxes)

        for dx, dy in DIRS:
            nx, ny = px + dx, py + dy

            if (nx, ny) in walls:
                continue
            if not in_bounds(nx, ny, cols, rows):
                continue

            if (nx, ny) in box_set:
                bx, by = nx + dx, ny + dy
                if (bx, by) in walls or (bx, by) in box_set:
                    continue
                if not in_bounds(bx, by, cols, rows):
                    continue

                new_boxes = list(boxes)
                idx = new_boxes.index((nx, ny))
                new_boxes[idx] = (bx, by)
                new_boxes.sort()
                new_state = ((nx, ny), tuple(new_boxes))
            else:
                new_state = ((nx, ny), tuple(boxes))

            if new_state not in visited:
                visited.add(new_state)
                q.append((new_state, steps + 1))

    return None, len(visited)


def is_deadlock(box_pos, walls_set, targets_set, cols, rows):
    """简单死锁检测：箱子在角落（两面墙形成直角）且不在目标点"""
    if box_pos in targets_set:
        return False
    x, y = box_pos

    # 只有最经典的角落死锁：两个垂直方向都是墙/边界
    corners = [
        ((0, -1), (-1, 0)),  # 上+左
        ((0, -1), (1, 0)),   # 上+右
        ((0, 1), (-1, 0)),   # 下+左
        ((0, 1), (1, 0)),    # 下+右
    ]
    for d1, d2 in corners:
        n1 = (x + d1[0], y + d1[1])
        n2 = (x + d2[0], y + d2[1])
        n1_blocked = n1 in walls_set or not in_bounds(n1[0], n1[1], cols, rows)
        n2_blocked = n2 in walls_set or not in_bounds(n2[0], n2[1], cols, rows)
        if n1_blocked and n2_blocked:
            return True
    return False


# ── 逆向拉箱生成器 ──────────────────────────────────────

def generate_by_reverse_pull(template, max_attempts=200):
    """
    使用逆向拉动法生成关卡。

    流程:
    1. 将箱子放在目标点上（已解状态）
    2. 随机选择一个箱子，模拟反向拉动
    3. 每次拉动后检查死锁
    4. 拉动足够次数后，BFS 验证
    5. 如果验证通过，返回关卡配置
    """
    cols = template["cols"]
    rows = template["rows"]
    walls = set(template["walls"])
    targets = template["targets"]
    num_pulls = template["num_pulls"]
    num_boxes = template["num_boxes"]

    # 如果目标点不是在开放地板上，则报错
    for tx, ty in targets:
        if (tx, ty) in walls:
            print(f"  [错误] Level {template['id']}: 目标点 ({tx},{ty}) 在墙上！")
            return None

    for attempt in range(max_attempts):
        # 初始状态：箱子在目标点上
        boxes = list(targets)[:num_boxes]
        random.shuffle(boxes)

        walls_set = set(walls)
        targets_set = set(tuple(t) for t in targets)
        boxes_set = set(boxes)

        # 玩家起始位置：放在某个箱子旁边（这样第一次拉动才有可能）
        # 先找出所有箱子周围的可站位置
        adjacent_to_boxes = []
        for bx, by in boxes:
            for d in DIRS:
                ax, ay = bx + d[0], by + d[1]
                if in_bounds(ax, ay, cols, rows) and (ax, ay) not in walls and (ax, ay) not in boxes:
                    adjacent_to_boxes.append((ax, ay))

        # 如果箱子周围有可站位置，随机选一个
        player = None
        if adjacent_to_boxes:
            adjacent_to_boxes = list(set(adjacent_to_boxes))
            random.shuffle(adjacent_to_boxes)
            for ap in adjacent_to_boxes:
                px, py = ap
                for d in DIRS:
                    # d 指向箱子方向: test_box = puller + d
                    test_box = (px + d[0], py + d[1])
                    if test_box in boxes:
                        # 玩家需要向反方向走一格(离开箱子):
                        # 玩家从 ap 移动到 ap - d (远离箱子)
                        behind = (ap[0] - d[0], ap[1] - d[1])
                        if in_bounds(behind[0], behind[1], cols, rows) \
                           and behind not in walls and behind not in boxes \
                           and behind not in targets:
                            player = ap
                            break
                if player:
                    break

        # 如果还是没找到，随便放一个空地
        if player is None:
            for _ in range(100):
                px = random.randint(1, cols - 2)
                py = random.randint(1, rows - 2)
                if (px, py) not in walls and (px, py) not in boxes:
                    player = (px, py)
                    break
        if player is None:
            continue

        walls_set = set(walls)
        targets_set = set(tuple(t) for t in targets)
        boxes_set = set(boxes)

        # 逆向拉动循环
        pulls_done = 0
        failed_paths = 0
        history = [(player, list(boxes))]
        max_pulls = num_pulls + 2
        loop_safety = 200  # 防止死循环

        while pulls_done < max_pulls and loop_safety > 0:
            loop_safety -= 1
            # 找出所有合法的拉动操作
            valid_pulls = []

            # 玩家走到每个箱子的相邻位置
            reachable = bfs_reachable(player, walls_set, boxes_set, cols, rows)

            # 更简单的：直接检查每个箱子，看玩家是否可以从相邻位置拉动它
            for bi, box in enumerate(boxes):
                bx, by = box
                # 四个方向：玩家需要站在箱子的对面，然后向后拉
                for d in DIRS:
                    # 玩家需要站在 (bx + dx, by + dy) 位置面向箱子
                    puller_pos = (bx + d[0], by + d[1])

                    # 检查拉动位置是否合法
                    if not in_bounds(puller_pos[0], puller_pos[1], cols, rows):
                        continue
                    if puller_pos in walls_set:
                        continue
                    # 玩家现在可以从当前位置走到拉动位置...
                    if puller_pos not in reachable:
                        continue

                    # == 逆向拉动公式 ==
                    # 玩家在 puller_pos，箱子在 (bx, by)，d = puller_pos - box
                    # 玩家需要"拉开"箱子：玩家向 d 方向再走一格，箱子跟到玩家原位置
                    # 玩家从 puller_pos → puller_pos + d（离开箱子更远）
                    # 箱子从 (bx, by) → puller_pos（跟到玩家原位置）
                    new_player = (puller_pos[0] + d[0], puller_pos[1] + d[1])
                    new_box = puller_pos

                    # 验证新玩家位置
                    if not in_bounds(new_player[0], new_player[1], cols, rows):
                        continue
                    if new_player in walls_set:
                        continue
                    if new_player in boxes_set:
                        continue

                    # 验证箱子新位置（puller_pos）没有被其他箱子占据
                    box_occupied = False
                    for oj, ob in enumerate(boxes):
                        if oj != bi and ob == new_box:
                            box_occupied = True
                            break
                    if box_occupied:
                        continue

                    # 拉动必须改变箱子位置
                    if new_box == box:
                        continue

                    # 死锁检测
                    if is_deadlock(new_box, walls_set, targets_set, cols, rows):
                        failed_paths += 1
                        continue

                    valid_pulls.append((bi, d, new_player, new_box))

            if not valid_pulls:
                # 没有有效拉动，检查是否已经拉够了
                if pulls_done >= num_pulls - 1:
                    break
                # 尝试回溯
                if len(history) > 1:
                    history.pop()
                    player, boxes = history[-1]
                    player = tuple(player)
                    boxes = [tuple(b) for b in boxes]
                    boxes_set = set(boxes)
                    pulls_done -= 1
                    continue
                else:
                    break

            # 选择拉动（根据复杂度偏向于选不同的箱子）
            if template["complexity"] > 0.5:
                # 高复杂度：优先拉动上次没动过的箱子
                recent_boxes = set()
                if len(history) >= 3:
                    _, prev_boxes = history[-1]
                    _, prev_boxes2 = history[-2]
                    for pb in [prev_boxes, prev_boxes2]:
                        for pb_box in pb:
                            recent_boxes.add(tuple(pb_box))

                # 按箱子去重分组
                box_choices = {}
                for bi, d, np, nb in valid_pulls:
                    if bi not in box_choices:
                        box_choices[bi] = []
                    box_choices[bi].append((bi, d, np, nb))

                # 优先选最近没动过的箱子
                if len(box_choices) > 1:
                    # 计算每个箱子最近被拉动的次数
                    box_recent = {}
                    for bi in range(len(boxes)):
                        count = sum(1 for h in history[-5:] for hb in h[1] if tuple(hb) == tuple(boxes[bi]))
                        box_recent[bi] = count
                    least_recent = min(box_recent, key=box_recent.get)
                    if least_recent in box_choices:
                        pull = random.choice(box_choices[least_recent])
                    else:
                        all_options = [p for choices in box_choices.values() for p in choices]
                        pull = random.choice(all_options)
                else:
                    pull = random.choice(valid_pulls)
            else:
                # 低复杂度：随机选择
                pull = random.choice(valid_pulls)

            bi, d, new_player, new_box = pull

            # 应用拉动
            old_box = boxes[bi]
            boxes[bi] = new_box
            player = new_player
            boxes_set = set(boxes)
            pulls_done += 1
            history.append((player, list(boxes)))

        # 检查是否达到目标拉动次数
        if pulls_done < num_pulls - 1:
            continue

        # 计算曼哈顿距离总和（衡量难度）
        total_md = sum(manhattan(boxes[i], targets[i % len(targets)]) for i in range(num_boxes))

        # BFS 验证
        grid = [[FLOOR] * cols for _ in range(rows)]
        for wx, wy in walls:
            grid[wy][wx] = WALL

        min_steps, visited_count = bfs_solve(grid, cols, rows, targets, player, boxes)

        # 检查可解性和难度评分
        if min_steps is not None and min_steps > 0:
            # 检查是否有箱子还在目标点上（不允许——关卡不能从半解状态开始）
            boxes_on_targets = sum(1 for b in boxes if b in targets_set)
            if boxes_on_targets > 0:
                continue

            # 难度下限：根据关卡难度参数设置最低步数要求
            min_required_steps = max(2, int(2 + template["complexity"] * 10 + template["oppression"] * 5))
            if min_steps < min_required_steps:
                continue

            # 记录难度评分
            difficulty = {
                "min_steps": min_steps,
                "visited_count": visited_count,
                "failed_paths": failed_paths,
                "total_manhattan": total_md,
                "attempt": attempt,
            }

            # 关卡就绪
            result = {
                "id": template["id"],
                "name": template["name"],
                "cols": cols,
                "rows": rows,
                "step_limit": template["step_limit"],
                "grid": [],
                "targets": targets,
                "_difficulty": difficulty,
            }

            # 根据 BFS 结果调整步数限制（对休闲玩家要宽松）
            suggested_limit = max(min_steps * 3 + 5, template["step_limit"])
            result["step_limit"] = suggested_limit

            # 构建最终 grid (包含箱子和玩家)
            final_grid = [[FLOOR] * cols for _ in range(rows)]
            for wx, wy in walls:
                final_grid[wy][wx] = WALL
            for bx, by in boxes:
                final_grid[by][bx] = BOX
            px, py = player
            final_grid[py][px] = PLAYER
            result["grid"] = final_grid

            return result

    return None


def bfs_reachable(start, walls_set, boxes_set, cols, rows):
    """BFS 查找玩家从起点可到达的所有位置（避开墙和箱子）"""
    if start is None:
        return set()
    visited = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not in_bounds(nx, ny, cols, rows):
                continue
            if (nx, ny) in walls_set:
                continue
            if (nx, ny) in boxes_set:
                continue
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny))
    return visited


# ── 主生成流程 ──────────────────────────────────────────

def generate_all_levels(seed=None):
    """生成全部 20 关"""
    if seed is not None:
        random.seed(seed)

    levels = []
    stats_summary = []

    for template in TEMPLATES:
        lid = template["id"]
        name = template["name"]
        opp = template["oppression"]
        comp = template["complexity"]

        print(f"正在生成第 {lid:2d} 关: {name}  (压抑={opp:.2f}, 复杂={comp:.2f})")

        result = generate_by_reverse_pull(template)

        if result is None:
            print(f"  ⚠ 未找到有效解！尝试放宽约束再次生成...")
            # 备用：直接手动设计一个简单关卡
            result = fallback_level(template)
            if result:
                print(f"  ✓ 使用备用方案")
            else:
                print(f"  ✗ 生成失败")
                continue

        # 输出统计
        diff = result["_difficulty"]
        min_s = diff["min_steps"]
        vis = diff["visited_count"]
        fail = diff["failed_paths"]
        md = diff["total_manhattan"]
        atm = diff["attempt"]
        print(f"  → 最短={min_s}步, 搜索节点={vis}, 失败路径={fail}, 曼哈顿={md} (尝试{atm+1}次)")

        # 删除临时字段
        del result["_difficulty"]

        levels.append(result)
        stats_summary.append({
            "id": lid,
            "name": name,
            "cols": template["cols"],
            "rows": template["rows"],
            "step_limit": template["step_limit"],
            "oppression": opp,
            "complexity": comp,
            "min_steps": min_s,
            "visited": vis,
            "failed_paths": fail,
            "manhattan": md,
        })

    return levels, stats_summary


def fallback_level(template):
    """
    备用方案：如果逆向拉动无法生成有效关卡，手动构建。
    使用简单的箱子和玩家布局，BFS确保可解。
    """
    cols = template["cols"]
    rows = template["rows"]
    walls = set(template["walls"])
    targets = template["targets"]
    num_boxes = len(targets)  # 箱子数 = 目标点数

    # 把箱子放在目标点旁边
    boxes = []
    for i in range(num_boxes):
        tx, ty = targets[i % len(targets)]
        # 在目标点旁边找个位置（不能重复放别的箱子）
        for d in DIRS:
            bx, by = tx + d[0], ty + d[1]
            if in_bounds(bx, by, cols, rows) and (bx, by) not in walls \
               and (bx, by) not in targets and (bx, by) not in boxes:
                boxes.append((bx, by))
                break
        else:
            # 实在不行放远一点
            boxes.append((tx - 1, ty))

    # 找一个角落放玩家
    player = None
    for y in range(1, rows - 1):
        for x in range(1, cols - 1):
            if (x, y) not in walls and (x, y) not in boxes and (x, y) not in targets:
                player = (x, y)
                break
        if player:
            break
    if player is None:
        return None

    # BFS验证
    grid = [[FLOOR] * cols for _ in range(rows)]
    for wx, wy in walls:
        grid[wy][wx] = WALL

    min_steps, visited_count = bfs_solve(grid, cols, rows, targets, player, boxes)
    if min_steps is None:
        # 再试一次换个位置
        for attempt in range(20):
            boxes = []
            for i in range(num_boxes):
                tx, ty = targets[i % len(targets)]
                placed = False
                for d in DIRS:
                    bx, by = tx + d[0], ty + d[1]
                    if in_bounds(bx, by, cols, rows) and (bx, by) not in walls \
                       and (bx, by) not in targets and (bx, by) not in boxes:
                        boxes.append((bx, by))
                        placed = True
                        break
                if not placed:
                    boxes.append((tx - 1, ty - 1))

            min_steps, _ = bfs_solve(grid, cols, rows, targets, player, boxes)
            if min_steps is not None:
                break

    if min_steps is None:
        return None

    final_grid = [[FLOOR] * cols for _ in range(rows)]
    for wx, wy in walls:
        final_grid[wy][wx] = WALL
    for bx, by in boxes:
        final_grid[by][bx] = BOX
    px, py = player
    final_grid[py][px] = PLAYER

    # 步数限制对休闲玩家要宽松
    new_step_limit = max(min_steps * 3 + 10, template["step_limit"])

    return {
        "id": template["id"],
        "name": template["name"],
        "cols": cols,
        "rows": rows,
        "step_limit": new_step_limit,
        "grid": final_grid,
        "targets": targets,
        "_difficulty": {"min_steps": min_steps, "visited_count": 0, "failed_paths": 0, "total_manhattan": 0, "attempt": 0},
    }


# ── 验证器 ──────────────────────────────────────────────

def validate_level(level):
    """验证关卡的有效性"""
    errors = []
    grid = level["grid"]
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    if rows != level["rows"] or cols != level["cols"]:
        errors.append(f"行列数不匹配: grid={rows}x{cols}, 声明={level['rows']}x{level['cols']}")

    player_count = sum(row.count(PLAYER) for row in grid)
    box_count = sum(row.count(BOX) for row in grid)

    if player_count != 1:
        errors.append(f"玩家数量: {player_count} (期望1)")
    if box_count != len(level["targets"]):
        errors.append(f"箱子数量: {box_count}, 目标点数量: {len(level['targets'])}")

    for tx, ty in level["targets"]:
        if not in_bounds(tx, ty, cols, rows):
            errors.append(f"目标点 ({tx},{ty}) 越界")
        elif grid[ty][tx] == WALL:
            errors.append(f"目标点 ({tx},{ty}) 在墙上")

    # 找玩家和箱子位置
    player_pos = None
    boxes = []
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == PLAYER:
                player_pos = (x, y)
            elif grid[y][x] == BOX:
                boxes.append((x, y))

    # BFS求解
    if not errors:
        min_steps, visited = bfs_solve(grid, cols, rows, level["targets"], player_pos, boxes)
        if min_steps is None:
            errors.append("关卡无解")
        else:
            level["_bfs_min_steps"] = min_steps
            level["_bfs_visited"] = visited

    return errors


# ── 主入口 ──────────────────────────────────────────────

def main():
    import os

    seed = 42  # 固定种子保证可复现
    print(f"使用随机种子: {seed}")
    print()

    levels, stats = generate_all_levels(seed=seed)

    if not levels:
        print("错误：没有成功生成任何关卡！")
        sys.exit(1)

    # 验证所有关卡
    print()
    print("=" * 60)
    print("验证所有关卡...")
    all_ok = True
    for level in levels:
        errs = validate_level(level)
        lid = level["id"]
        name = level["name"]
        bms = level.get("_bfs_min_steps", "?")
        if not errs:
            print(f"  ✓ Level {lid:2d} ({name}): 可解, 最短{bms}步")
        else:
            print(f"  ✗ Level {lid:2d} ({name}): {'; '.join(errs)}")
            all_ok = False
        # 清理临时字段
        level.pop("_bfs_min_steps", None)
        level.pop("_bfs_visited", None)

    if not all_ok and len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("存在错误但 --force 标志已设置，继续写入...")
    elif not all_ok:
        print()
        print("有些关卡未通过验证。使用 --force 参数强制写入。")
        sys.exit(1)

    # 写入 levels.json
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "levels.json")
    output = {"levels": levels}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print(f"✓ 已写入: {output_path}")
    print(f"  共 {len(levels)} 关")

    # 输出统计表
    print()
    print("=" * 60)
    print(f"{'ID':>3} {'名称':<16} {'尺寸':<7} {'压抑':<6} {'复杂':<6} {'步限':<6} {'最短':<6} {'搜索':<7}")
    print("-" * 60)
    for s in stats:
        print(f"{s['id']:>3} {s['name']:<16} {s['cols']}x{s['rows']:<4} "
              f"{s['oppression']:<6.2f} {s['complexity']:<6.2f} "
              f"{s['step_limit']:<6} {s['min_steps']:<6} {s['visited']:<7}")
    print("=" * 60)


if __name__ == "__main__":
    main()
