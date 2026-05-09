# aisokoban 项目状态摘要

## 总体进度
```
Step 1-5: ✅ 主线20关 / 对话 / 沙盒模式
Step 6:   ✅ SLC解析器 + BFS优化 + 38157关社区库导入
下一步:     讨论4个方向 → 决定推进路径
```

## 工具链
- `tools/slc_parser.py` — 解析 SLC/文本格式，支持 `--dir` 批量导入，`--verify` BFS验证
- `tools/bfs_solver.py` — 带角死锁检测的 BFS 求解器，复杂关卡(>4箱)自动跳过
- `tools/sokoban_generator.py` — 逆向拉动法关卡生成器

## 关键数据
- 主线: 20关 (levels.json)
- 沙盒: 6关 (sandbox.json, IDs 101-106)
- 社区库: 38,157关 (reference/38168/, 463个TXT文件)
  - 小关卡(≤4箱, ≤100格): 3,222关 → BFS可验证
  - 大关卡: 34,935关 → 跳过BFS
- JSON输出: 163MB (tmp)

## 待讨论4个方向
1. 难度筛选 + 剧情分配
2. 剧情联动（动态关卡池）
3. 覆盖面统计
4. 沙盒模式扩展

## Git
- 远程: https://github.com/TerryZ874/SokobanStory.git
- 工作流: Claude commit/push, 用户用 GitHub Desktop 查看
