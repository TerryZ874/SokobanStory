# AISokoban — 推箱子游戏实现方案

## 一、架构总览

```
aisokoban/
├── .godot/                  # Godot 引擎自动生成
├── assets/                  # 美术资源
│   ├── tiles/               # 瓦片图（地板、墙、目标点）
│   └── sprites/             # 玩家、箱子精灵图
├── data/                    # 关卡数据（JSON）
│   ├── levels.json          # 所有关卡定义
│   └── progress.json        # 玩家通关进度存档
├── scenes/                  # Godot 场景
│   ├── main.tscn            # 主菜单场景
│   ├── game.tscn            # 游戏主场景
│   ├── level_select.tscn    # 关卡选择界面
│   └── hud.tscn             # 游戏内 HUD（步数显示、菜单按钮）
├── scripts/                 # GDScript 脚本
│   ├── autoload/
│   │   ├── game_state.gd    # 全局游戏状态（当前关卡、步数、解锁进度）
│   │   └── level_data.gd    # 关卡数据加载器
│   ├── game/
│   │   ├── board.gd         # 游戏棋盘逻辑
│   │   ├── player.gd        # 玩家角色控制
│   │   └── box.gd           # 箱子逻辑
│   └── ui/
│       ├── hud.gd           # HUD 控制
│       └── level_select.gd  # 关卡选择控制
├── default_env.tres         # 环境配置
├── project.godot            # Godot 项目文件
└── icon.png                 # 应用图标
```

---

## 二、数据组织（JSON 关卡格式）

### 2.1 关卡定义文件 `data/levels.json`

```json
{
  "levels": [
    {
      "id": 1,
      "name": "第一关：初识推箱",
      "cols": 8,
      "rows": 8,
      "step_limit": 20,
      "grid": [
        [1, 1, 1, 1, 1, 0, 0, 0],
        [1, 0, 0, 0, 1, 0, 0, 0],
        [1, 0, 3, 0, 1, 0, 0, 0],
        [1, 0, 0, 0, 1, 1, 1, 1],
        [1, 0, 0, 0, 2, 0, 0, 1],
        [1, 1, 0, 0, 0, 0, 0, 1],
        [0, 1, 0, 0, 0, 0, 0, 1],
        [0, 1, 1, 1, 1, 1, 1, 1]
      ],
      "targets": [
        [3, 3],
        [4, 4]
      ]
    }
  ]
}
```

| 数值 | 含义       | 说明                     |
|------|------------|--------------------------|
| 0    | 空地(FLOOR) | 可通行区域               |
| 1    | 墙(WALL)    | 不可通行                 |
| 2    | 箱子(BOX)   | 可推动                   |
| 3    | 玩家(PLAYER)| 初始玩家位置             |

- **targets**: 所有目标点的坐标 `[col, row]` 数组（左上角为 0,0）
- **step_limit**: 步数上限，玩家步数超过即失败
- 箱子和玩家的初始位置直接在 `grid` 里定义，`targets` 单独列出

### 2.2 为什么用 JSON 而非 CSV

| 方面       | JSON                     | CSV                        |
|------------|--------------------------|----------------------------|
| 可读性     | 结构清晰，层级直观       | 二维表，行列含义模糊       |
| 扩展性     | 容易加字段（step_limit、targets） | 加一列就要改所有行 |
| 多关卡     | 天然数组支持             | 需要分隔文件或多个 sheet   |
| 错误容忍   | 格式错误直接报错         | 引号/逗号问题容易静默解析错 |

**结论：JSON 更合适。** 直接用任何文本编辑器修改 `levels.json` 即可改关卡，无需打开 Godot。

### 2.3 进度存档 `data/progress.json`

```json
{
  "unlocked_levels": [1, 2],
  "completed_levels": {
    "1": { "best_steps": 12, "completed": true },
    "2": { "best_steps": null, "completed": false }
  }
}
```

---

## 三、代码组织与核心逻辑

### 3.1 Autoload（全局单例）

**`level_data.gd`** — 关卡数据加载器
- 在 `_ready()` 中读取 `data/levels.json`
- 暴露函数 `get_level(id: int) -> Dictionary`
- 负责数据合法校验（行列数匹配、targets 是否在空地等）

**`game_state.gd`** — 游戏状态管理
- 当前关卡 ID、当前步数、步数上限
- 胜负判定逻辑
- 读取/写入 `progress.json`

### 3.2 Game 场景主要脚本

**`board.gd`** — 棋盘核心逻辑（挂在 game 场景的根节点）

```
board.gd 职责:
├── 初始化: 读取 JSON → 在 TileMap 上绘制地图
├── 运行时维护二维数组 grid_state（记录空地/墙/箱子/玩家）
├── 查询: get_cell(col, row) → 格子类型
├── 移动判定: can_move(col, row, direction) → bool
│   ├── 目标格是墙 → 不可移动
│   ├── 目标格是箱子 → 递归判定箱子能否被推动
│   └── 箱子推出边界/撞墙 → 不可推动
├── 执行移动: move_player(direction) → bool
│   ├── 更新玩家坐标
│   ├── 若有箱子被推动，更新箱子坐标 + grid_state
│   ├── 步数 +1
│   └── 发射 signal("step_count_updated", steps)
└── 胜负判定: check_win_condition() / check_fail_condition()
    ├── 胜利: 所有 target 坐标上都有箱子
    ├── 失败: steps > step_limit && !胜利
    └── 任一满足 → 发射 signal("game_over", result)
```

**`player.gd`** — 玩家输入处理（挂在 Player 节点上）
- 监听键盘输入（WASD / 方向键）
- 调用 `board.move_player(direction)`
- 实现移动动画（Tween 平滑滑动）
- 移动完成前屏蔽新输入（防止连按穿墙）

**`box.gd`** — 箱子（挂在每个 Box 节点上）
- 保存自身 grid 坐标
- 移动时播放 Tween 动画
- 当箱子上方有目标点时改变颜色/闪烁（视觉反馈）

### 3.3 胜负判定核心伪代码

```gdscript
# board.gd — check_win_condition()
func check_win_condition() -> bool:
    for target in current_level.targets:
        var x = target[0]
        var y = target[1]
        if grid_state[y][x] != CELL.BOX:
            return false
    return true

func check_fail_condition() -> bool:
    return current_steps > step_limit and not check_win_condition()

# game_state.gd — 每步移动后调用
func on_step_taken():
    if board.check_win_condition():
        emit_signal("game_victory")
    elif current_steps > step_limit:
        emit_signal("game_over_by_steps")
```

**关键设计决策**：步数超过上限后不立即结束，只有不满足胜利条件时才判负。即：最后一步刚好把箱子推上最后一个目标点同时步数用完 → 胜利。

### 3.4 撤回功能（Undo）

```
undo 系统:
├── board 维护一个移动历史栈
│   ├── push_history(move_record): 每次移动后记录 { player_pos, box_positions }
│   └── undo(): 弹出栈顶记录，恢复状态
├── 步数同步回退（步数 -= 1）
└── UI 上的"撤回"按钮绑定 board.undo()
```

---

## 四、美术资源管理

### 4.1 推荐策略：程序化绘制（零美术资源也能开工）

游戏初期不需要任何外部图片资源。使用 `ColorRect` + 简单形状即可。

| 元素   | 实现方式                    | 颜色          |
|--------|-----------------------------|---------------|
| 地板   | ColorRect / TileMap 默认    | #2d2d2d 深灰  |
| 墙     | ColorRect                   | #4a4a4a 中灰  |
| 箱子   | ColorRect + 描边            | #d4a574 棕色  |
| 目标点 | ColorRect + 虚线/闪烁圆圈   | #ff6b6b 红色  |
| 玩家   | ColorRect + 箭头/圆点       | #4ecdc4 青色  |
| 正确箱子| 箱子上叠加半透明绿色遮罩    | rgba(0,255,0,0.3) |

### 4.2 后续美术替换

当有了美术资源后，只需在 `assets/tiles/` 和 `assets/sprites/` 下放图片文件，然后在 Godot 编辑器中把 ColorRect 替换为 TextureRect / Sprite2D 即可。**数据逻辑层完全不受影响。**

### 4.3 TileMap 方案（推荐）

用 **TileSet** 替代零散的 ColorRect：
- 一个 tileset 图片包含所有瓦片（16×16 或 32×32）
- `board.gd` 初始化时按 grid 数据刷 TileMap
- 性能更好，渲染合并，适合关卡制游戏

---

## 五、场景树结构

### Game.tscn 场景树

```
Game (Node2D)  ← board.gd
├── TileMap                # 绘制地板和墙（z_index = 0）
├── BoxContainer           # 箱子容器（z_index = 1）
│   ├── Box (Area2D)      # 每个箱子独立节点
│   │   ├── Sprite2D / ColorRect
│   │   └── CollisionShape2D
│   ├── Box
│   └── ...
├── Player (KinematicBody2D / CharacterBody2D)
│   ├── Sprite2D / ColorRect
│   ├── CollisionShape2D
│   └── player.gd
└── CanvasLayer            # UI 层，不随镜头移动
    └── HUD                # hud.gd
        ├── StepCounter (Label): "步数: 12 / 20"
        ├── UndoButton (Button)
        ├── RestartButton (Button)
        └── BackButton (Button) → 返回关卡选择
```

### 层级关系

```
Main.tscn (主菜单)
  └─ "开始游戏" → LevelSelect.tscn
                    └─ 选择关卡 → Game.tscn (加载对应 level ID)
                                     └─ 过关/超步 → 弹窗 → LevelSelect / 重试
```

---

## 六、输入处理方案

```
玩家输入:
├── 物理按键: 方向键 ↑↓←→  /  WASD
├── 虚拟按钮（触屏/H5）: 屏幕方向按钮（可用于导出到移动端）
├── 移动方式: 基于网格的离散移动（非自由移动）
│   └── 每按一次方向键 → 走一格
└── 快捷键:
    ├── Ctrl+Z / Z → 撤回
    └── R → 重新开始
```

---

## 七、分阶段实现计划

### Phase 1 — 最小可玩原型（~2-3 小时）
1. 创建 Godot 4 项目，写好 `project.godot`
2. 实现 `level_data.gd`：读取 `levels.json`，解析关卡
3. 实现 `board.gd`：在 TileMap 上画出地图，维护 grid_state
4. 实现 `player.gd`：方向键移动，墙壁碰撞检测
5. 实现箱子推动逻辑（推动一个箱子、连锁推动不做）
6. 实现 HUD 显示步数
7. 实现胜利/失败判定和弹窗提示
8. **手动创建 3 个关卡验证完整流程**

### Phase 2 — 完善功能（~2 小时）
1. 关卡选择界面
2. 撤回功能（Undo）
3. 步数上限失败判定
4. 进度保存（localStorage / 文件）
5. 重开当前关卡

### Phase 3 — 打磨（可选）
1. 移动动画（Tween 平滑移动）
2. 音效（箱子落地声、胜利声）
3. 关卡编辑器（可选但不在当前范围内）
4. 更多关卡（经典 Sokoban 关卡库有现成的）

---

## 八、潜在坑点与应对

| 坑点 | 应对方案 |
|------|----------|
| 连按导致穿墙 | 移动动画期间屏蔽输入；用 `is_moving` flag 控制 |
| 箱子被推出边界 | `can_move()` 做边界检查：x,y 在 [0, cols-1] × [0, rows-1] 内 |
| 两个箱子互相卡死（传统 Sokoban 不允许同时推两个箱子） | `can_move()` 只处理单箱子推动，第二个箱子挡路直接返回 false |
| JSON 格式错误导致游戏崩溃 | `level_data.gd` 加 try-catch，失败时弹窗提示 JSON 第几行有问题 |
| 步数统计不准 | 只在 `move_player()` 成功后 +1，撤回时 -1，不做额外的计数逻辑 |

---

## 九、JSON 关卡编辑说明（写给非程序员）

在 `data/levels.json` 中：

```
数字含义：
  0 = 空地（人和箱子可以站）
  1 = 墙（不能穿过）
  2 = 箱子（可以推）
  3 = 玩家起点

targets 是目标点坐标，格式 [列, 行]。
左上角是 [0, 0]，往右 x 增加，往下 y 增加。

step_limit 是步数上限。

编辑关卡步骤：
1. 用记事本/VSCode 打开 data/levels.json
2. 复制最后一个关卡的大括号段（从 { 到 }），在它后面粘贴
3. 修改 id、name 和 grid 内容
4. 确保 targets 坐标对应到 grid 中你想放置目标点的位置
5. 注意 grid 的数组行列数与 cols/rows 一致
6. 保存文件，重新打开游戏即可
```

**示例：编辑一个 4×4 的小关卡**

```
"grid": [
  [1, 1, 1, 1],
  [1, 3, 0, 1],
  [1, 0, 2, 1],
  [1, 1, 1, 1]
],
"targets": [[2, 2]],
"step_limit": 5
```

玩家在 (1,1)，箱子在 (2,2)，目标点也在 (2,2)，5 步内把箱子推到目标。
