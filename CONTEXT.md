# aisokoban 项目状态摘要

## 总体进度
```
Step 1: ✅ 分层渲染 + 分辨率 + UI 重构
Step 2: ✅ 对话系统 + 前3关剧情
Step 3: ✅ Chapter 1 关卡设计 (4-20关) + BFS 验证（所有关卡可解）
Step 4: ⏳ 平衡性 + 整合测试（待开始）
```

## Git 仓库
- 远程：`https://github.com/TerryZ874/SokobanStory.git`
- 本地：`/Users/saoteman/AIProjects/aisokoban/`
- 工作流：我（Claude）负责 commit/push，用户用 GitHub Desktop 查看历史
- 最近的推送尚未成功（HTTP2 网络错误），需要重试

## 已完成功能

### 渲染系统
- 四层 z_index 容器结构：FloorContainer(0) → TargetContainer(1) → WallContainer(2) → EntityContainer(3)
- 1920×1080 分辨率，动态 TILE_SIZE
- 所有元素用 ColorRect/Area2D 节点，无 draw_rect
- 未来替换美术时只需替换各层子节点

### 核心逻辑
- 方向键/ WASD 移动
- Z 撤回，R 重开
- 步数限制 + 胜利/失败检测
- JSON 关卡数据加载（data/levels.json，当前 3 关）
- 存档系统（user://progress.json）

### UI
- 主菜单：标题 + 开始游戏 + 退出（1920×1080 居中）
- HUD：关卡名、步数计数、撤回/重来/返回按钮
- 胜利弹窗：下一关、重玩、返回菜单
- 失败弹窗：重试、返回菜单

### 对话系统
- 对话场景（dialogue.tscn）：底部面板、角色名、文本、插图描述
- 点击/空格/回车推进，ESC/按钮跳过
- 对话结束后自动加载下一关或返回主菜单
- 剧情数据（data/story.json）：4 个角色 + 3 关对话

### 角色定义
| 代号 | 名字 | 性别 | 说明 |
|-----|------|------|------|
| c01 | 林远 | 男 | 主角，前程序员意识体 |
| c02 | 伊芙 | 女 | 引导员，温和但有所隐瞒 |
| c03 | 系统 | - | 底层系统广播，冷漠 |
| c04 | 老周 | 男 | 资深意识体，揭示算力真相 |

### Autoloads
- `level_data` → scripts/autoload/level_data.gd
- `game_state` → scripts/autoload/game_state.gd
- `story_data` → scripts/autoload/story_data.gd

## GDD（设计文档）
- `GDD/sokoban_gdd.md` — 完整的设计文档
- 100关，5章节，每20关一个故事弧
- 2050年意识体世界，推箱子生产算力
- "妈妈"是最高智慧意识体
- 5名主角，第100关汇合反转

## 历史记录（重要决策）
1. 用户用 GitHub Desktop 查看提交历史，我负责所有 git 操作，无需询问
2. 不提前设计全部 100 关和剧情 — 先以前 20 关为标准，跑通从 0 到 1 的闭环
3. 用户要求分步迭代：Step 1 → 测试 → Step 2 → 测试 → Step 3 → ...

## 代码文件结构
```
aisokoban/
├── project.godot
├── data/
│   ├── levels.json          # 现有关卡（3关）
│   └── story.json           # 剧情数据（4角色 + 3关对话）
├── scenes/
│   ├── main.tscn            # 主菜单
│   ├── game.tscn            # 游戏主场景（含4层容器 + HUD）
│   └── dialogue.tscn        # 对话场景
├── scripts/
│   ├── autoload/
│   │   ├── level_data.gd    # 关卡数据加载器
│   │   ├── game_state.gd    # 游戏状态 + 对话流程控制
│   │   └── story_data.gd    # 故事数据加载器
│   ├── game/
│   │   ├── board.gd         # 核心棋盘逻辑（分层渲染、移动、推箱子）
│   │   ├── player.gd        # 玩家占位脚本
│   │   └── box.gd           # 箱子脚本（目标点变色）
│   └── ui/
│       ├── hud.gd           # HUD控制 + 弹窗逻辑
│       ├── main.gd          # 主菜单控制
│       └── dialogue.gd      # 对话控制（主题样式在代码中设置）
├── GDD/
│   └── sokoban_gdd.md       # 游戏设计文档
└── CONTEXT.md               # 本文件（项目状态摘要）
```
