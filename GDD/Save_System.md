# 存档系统设计文档

## 概述

游戏使用 Godot 的 `FileAccess` API，将存档写入 `user://save.json`（各平台用户目录，非游戏安装目录）。

存档仅用于主线模式，沙盒模式不触发任何存档操作。

---

## 数据结构

```json
{
  "current_level": 1,
  "completed_levels": [1, 2, 3],
  "player_difficulty": {
    "4": 2,
    "5": 5
  },
  "game_completed": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `current_level` | int | 玩家当前所在关，继续游戏时从此关开始 |
| `completed_levels` | int[] | 已通关的关卡 ID 列表 |
| `player_difficulty` | dict | 玩家主观评分，key 为关卡 ID 的字符串，value 为 1-10 |
| `game_completed` | bool | 是否通关全部 20 关主线 |

---

## 自动存档时机

| 触发点 | 行为 |
|--------|------|
| 进入新关卡（`board.gd start_level`） | 更新 `current_level` 并写入 |
| 胜利过关（`game_state.level_completed`） | 将当前关加入 `completed_levels`，检查是否通关全部关卡，写入 |

---

## 玩家评分

- 在游戏 HUD 左上角，点击 **"玩家难度"** 标签
- 弹出 1-10 评分按钮，选择后立即写入存档
- 再次进入该关卡时显示已评分数
- 评分可随时修改，后一次覆盖前一次

---

## 主菜单行为

| 按钮 | 有存档时 | 无存档时 |
|------|---------|---------|
| **继续游戏** (绿色) | 显示，从 `current_level` 继续 | 隐藏 |
| **继续游戏+** (绿色) | 通关后显示，从 `current_level` 继续 | 隐藏 |
| **新游戏** | 弹出确认框"是否删除存档并开始新游戏？" | 直接开始第 1 关 |

---

## 存档删除

触发时机：玩家在主菜单点击 **新游戏** → **确认**。

删除时调用 `DirAccess.remove_absolute("user://save.json")`，游戏从头开始。

---

## 代码结构

```
scripts/autoload/save_manager.gd    # 存档读写核心（autoload 单例）
scripts/autoload/game_state.gd      # 胜利时调用 save_manager.set_level_completed()
scripts/game/board.gd               # 进入关卡时调用 save_manager.save_game()
scripts/ui/hud.gd                   # 点击玩家难度标签 → 评分 → 保存
scripts/ui/main.gd                  # 继续/新游戏按钮逻辑
```

---

## 后续可扩展方向

- 每关的步数记录 / 最优步数
- 多个存档槽位
- 存档不同步到云端
