extends Node2D

enum CELL { FLOOR, WALL, BOX, PLAYER }

const GAME_W := 1920
const GAME_H := 1080

var level: Dictionary
var grid_state: Array
var player_pos := Vector2.ZERO
var player_node: Area2D
var boxes: Array = []
var box_positions: Array = []
var targets: Array = []
var current_steps := 0
var is_moving := false
var game_over := false
var move_history: Array = []
var board_offset := Vector2.ZERO
var tile_size := 64

@onready var floor_container = $FloorContainer
@onready var wall_container = $WallContainer
@onready var target_container = $TargetContainer
@onready var entity_container = $EntityContainer
@onready var hud = $CanvasLayer/HUD

func _ready():
	start_level(game_state.current_level_id)

func _compute_tile_size(rows: int, cols: int) -> int:
	var avail_w = GAME_W - 120
	var avail_h = GAME_H - 160
	var max_tile_w = avail_w / cols if cols > 0 else avail_w
	var max_tile_h = avail_h / rows if rows > 0 else avail_h
	return max(16, min(max_tile_w, max_tile_h))

func _unhandled_input(event: InputEvent):
	var ke := event as InputEventKey
	if ke == null or not ke.pressed or ke.echo:
		return
	if is_moving or game_over:
		return

	var dir := Vector2.ZERO
	match ke.keycode:
		KEY_UP, KEY_W:
			dir = Vector2.UP
		KEY_DOWN, KEY_S:
			dir = Vector2.DOWN
		KEY_LEFT, KEY_A:
			dir = Vector2.LEFT
		KEY_RIGHT, KEY_D:
			dir = Vector2.RIGHT
		KEY_Z:
			undo()
			return
		KEY_R:
			restart_level()
			return

	if dir != Vector2.ZERO:
		move_player(dir)

func _grid_to_pixel(col: float, row: float) -> Vector2:
	return Vector2(
		board_offset.x + col * tile_size + tile_size / 2,
		board_offset.y + row * tile_size + tile_size / 2
	)

func start_level(level_id: int):
	level = level_data.get_level(level_id)
	if level.is_empty():
		return

	_clear_board()

	game_state.current_level_id = level_id
	grid_state = []
	targets = []
	boxes = []
	box_positions = []
	move_history = []
	current_steps = 0
	is_moving = false
	game_over = false

	for t in level.targets:
		targets.append(Vector2(t[0], t[1]))

	for row in level.grid:
		var r = []
		for v in row:
			r.append(int(v))
		grid_state.append(r)

	tile_size = _compute_tile_size(level.rows, level.cols)
	board_offset = Vector2(
		(GAME_W - level.cols * tile_size) / 2,
		(GAME_H - level.rows * tile_size) / 2
	)

	_render_board()
	_create_player_and_boxes()
	_clear_grid_state_entities()
	_update_box_visuals()

	hud.update_level_info(level.name)
	hud.update_step_count(current_steps, level.step_limit)
	hud.hide_overlays()

func _clear_board():
	if player_node:
		player_node.queue_free()
		player_node = null
	for c in entity_container.get_children():
		c.queue_free()
	for c in wall_container.get_children():
		c.queue_free()
	for c in target_container.get_children():
		c.queue_free()
	for c in floor_container.get_children():
		c.queue_free()

func _render_board():
	var fg = ColorRect.new()
	fg.size = Vector2(level.cols * tile_size, level.rows * tile_size)
	fg.position = board_offset
	fg.color = Color("#2d2d2d")
	floor_container.add_child(fg)

	for row in level.rows:
		for col in level.cols:
			if grid_state[row][col] == CELL.WALL:
				var w = ColorRect.new()
				w.size = Vector2(tile_size, tile_size)
				w.position = board_offset + Vector2(col * tile_size, row * tile_size)
				w.color = Color("#999999")
				wall_container.add_child(w)

	for t in targets:
		var m = ColorRect.new()
		var s = tile_size * 0.5
		m.size = Vector2(s, s)
		m.position = board_offset + Vector2(t.x * tile_size + (tile_size - s) * 0.5, t.y * tile_size + (tile_size - s) * 0.5)
		m.color = Color("#ff6b6b")
		target_container.add_child(m)

func _create_player_and_boxes():
	for row in level.rows:
		for col in level.cols:
			var cell = grid_state[row][col]
			if cell == CELL.PLAYER:
				_make_player(col, row)
			elif cell == CELL.BOX:
				_make_box(col, row)

func _make_player(col: int, row: int):
	player_node = Area2D.new()
	player_node.position = _grid_to_pixel(col, row)
	player_pos = Vector2(col, row)

	var vis = ColorRect.new()
	vis.size = Vector2(tile_size - 8, tile_size - 8)
	vis.position = Vector2(-(tile_size - 8) / 2, -(tile_size - 8) / 2)
	vis.color = Color("#4ecdc4")
	player_node.add_child(vis)

	var col_shape = CollisionShape2D.new()
	var shape = RectangleShape2D.new()
	shape.size = Vector2(tile_size - 8, tile_size - 8)
	col_shape.shape = shape
	player_node.add_child(col_shape)

	entity_container.add_child(player_node)

func _make_box(col: int, row: int):
	var b = Area2D.new()
	b.position = _grid_to_pixel(col, row)

	var vis = ColorRect.new()
	vis.size = Vector2(tile_size - 8, tile_size - 8)
	vis.position = Vector2(-(tile_size - 8) / 2, -(tile_size - 8) / 2)
	vis.color = Color("#d4a574")
	b.add_child(vis)

	var col_shape = CollisionShape2D.new()
	var shape = RectangleShape2D.new()
	shape.size = Vector2(tile_size - 8, tile_size - 8)
	col_shape.shape = shape
	b.add_child(col_shape)

	var bs = preload("res://scripts/game/box.gd")
	b.set_script(bs)

	entity_container.add_child(b)
	boxes.append(b)
	box_positions.append(Vector2(col, row))

func _clear_grid_state_entities():
	for row in level.rows:
		for col in level.cols:
			if grid_state[row][col] in [CELL.PLAYER, CELL.BOX]:
				grid_state[row][col] = CELL.FLOOR

func move_player(direction: Vector2):
	if is_moving or game_over:
		return

	var target = player_pos + direction
	var tx = int(target.x)
	var ty = int(target.y)

	if tx < 0 or tx >= level.cols or ty < 0 or ty >= level.rows:
		return
	if grid_state[ty][tx] == CELL.WALL:
		return

	var box_idx = _get_box_at(target)
	if box_idx >= 0:
		var bnew = target + direction
		var bx = int(bnew.x)
		var by = int(bnew.y)

		if bx < 0 or bx >= level.cols or by < 0 or by >= level.rows:
			return
		if grid_state[by][bx] == CELL.WALL:
			return
		if _get_box_at(bnew) >= 0:
			return

		_save_snapshot()
		box_positions[box_idx] = bnew
		player_pos = target
		current_steps += 1

		var tween = create_tween().set_parallel(true)
		tween.tween_property(boxes[box_idx], "position", _grid_to_pixel(bx, by), 0.1)
		tween.tween_property(player_node, "position", _grid_to_pixel(tx, ty), 0.1)
		is_moving = true
		tween.finished.connect(_on_tween_done)

		_update_box_visuals()
		hud.update_step_count(current_steps, level.step_limit)
		_check_game_state()
		return

	if grid_state[ty][tx] == CELL.FLOOR:
		_save_snapshot()
		player_pos = target
		current_steps += 1

		var tween = create_tween()
		tween.tween_property(player_node, "position", _grid_to_pixel(tx, ty), 0.1)
		is_moving = true
		tween.finished.connect(_on_tween_done)

		hud.update_step_count(current_steps, level.step_limit)
		_check_game_state()

func _get_box_at(grid_pos: Vector2) -> int:
	for i in box_positions.size():
		if box_positions[i] == grid_pos:
			return i
	return -1

func _save_snapshot():
	move_history.append({
		player_pos = player_pos,
		box_positions = box_positions.duplicate(),
		steps = current_steps
	})

func undo():
	if move_history.is_empty() or is_moving or game_over:
		return

	var snap = move_history.pop_back()
	player_pos = snap.player_pos
	box_positions = snap.box_positions.duplicate()
	current_steps = snap.steps

	player_node.position = _grid_to_pixel(player_pos.x, player_pos.y)
	for i in boxes.size():
		boxes[i].position = _grid_to_pixel(box_positions[i].x, box_positions[i].y)

	_update_box_visuals()
	hud.update_step_count(current_steps, level.step_limit)

func _update_box_visuals():
	for i in boxes.size():
		var on_target = box_positions[i] in targets
		boxes[i].is_on_target = on_target

func _check_game_state():
	var won = true
	for t in targets:
		if t not in box_positions:
			won = false
			break

	if won:
		game_over = true
		await get_tree().create_timer(0.5).timeout
		hud.show_victory()
		game_state.level_completed(level.id, current_steps)
		return

	if current_steps > level.step_limit:
		game_over = true
		hud.show_defeat()

func _on_tween_done():
	is_moving = false

func restart_level():
	start_level(level.id)
