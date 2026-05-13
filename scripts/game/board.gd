extends Node2D

enum CELL { FLOOR, WALL, BOX, PLAYER }

const GAME_W := 1920
const GAME_H := 1080
const H_MARGIN := 120
const V_MARGIN := 160
const PLAYER_TEX := preload("res://art_assets/player_idle.PNG")
const ATLAS_TEX := preload("res://art_assets/enviroment/bg_package.PNG")

var level: Dictionary
var grid_state: Array
var player_pos := Vector2.ZERO
var player_node: Area2D
var boxes: Array = []
var box_positions: Array = []
var targets: Array = []
var current_steps := 0:
	set(value):
		current_steps = value
		_update_player_color()
var is_moving := false
var _player_body: Node2D
var _push_previews: Array = []
var _reach_previews: Array = []
var _is_auto_walking := false
var _current_push_dests: Dictionary = {}
var _current_dot_positions: Dictionary = {}
var _pushable_boxes: Array = []
var _pulse_time := 0.0
var _movement_timer := 0.0
signal player_moved
var game_over := false
var move_history: Array = []
var player_pivot: Node2D
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
	var avail_w = GAME_W - H_MARGIN
	var avail_h = GAME_H - V_MARGIN
	var max_tile_w = avail_w / cols if cols > 0 else avail_w
	var max_tile_h = avail_h / rows if rows > 0 else avail_h
	return max(16, min(max_tile_w, max_tile_h))

func _process(delta):
	if game_over:
		return
	_pulse_time += delta
	var t = (sin(_pulse_time * TAU) + 1.0) * 0.5
	var s = lerp(0.9, 1.0, t)

	# Pulse pushable boxes
	for idx in _pushable_boxes:
		if idx < boxes.size():
			boxes[idx].scale = Vector2(s, s)

	# Reset non-pushable boxes
	for i in boxes.size():
		if not i in _pushable_boxes:
			boxes[i].scale = Vector2.ONE

	if _movement_timer > 0:
		_movement_timer -= delta
		if _movement_timer <= 0:
			is_moving = false

func _unhandled_input(event: InputEvent):
	var ke := event as InputEventKey
	if ke == null or not ke.pressed or ke.echo:
		return

	if ke.keycode == KEY_ESCAPE:
		if not game_over:
			hud._toggle_pause()
		return

	if is_moving or game_over or _is_auto_walking:
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
		return

func _input(event: InputEvent):
	var me := event as InputEventMouseButton
	if me == null or not me.pressed or me.button_index != MOUSE_BUTTON_LEFT:
		return
	if is_moving or game_over or _is_auto_walking:
		return

	var grid = _pixel_to_grid(get_global_mouse_position())
	var gx := int(grid.x)
	var gy := int(grid.y)
	if gx < 0 or gx >= level.cols or gy < 0 or gy >= level.rows:
		return
	var gp := Vector2(gx, gy)

	# Click on adjacent pushable box → push
	var dir = gp - player_pos
	if dir in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
		var box_idx = _get_box_at(gp)
		if box_idx >= 0:
			var bnew = gp + dir
			var bx = int(bnew.x)
			var by = int(bnew.y)
			if not (bx < 0 or bx >= level.cols or by < 0 or by >= level.rows or grid_state[by][bx] != CELL.FLOOR or _get_box_at(bnew) >= 0):
				move_player(dir)
				get_viewport().set_input_as_handled()
				return

	# Any click on map → try to walk there
	_walk_to(gp)
	get_viewport().set_input_as_handled()

func _grid_to_pixel(col: float, row: float) -> Vector2:
	return Vector2(
		board_offset.x + col * tile_size + tile_size / 2,
		board_offset.y + row * tile_size + tile_size / 2
	)

func _pixel_to_grid(pixel: Vector2) -> Vector2:
	return Vector2(
		floor((pixel.x - board_offset.x) / tile_size),
		floor((pixel.y - board_offset.y) / tile_size)
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
	_pulse_time = 0.0
	_movement_timer = 0.0

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
	_update_player_color()

	# Player pulse animation to highlight which character you control
	if player_pivot:
		var tw = create_tween()
		tw.tween_property(player_pivot, "scale", Vector2(1.5, 1.5), 0.2)
		tw.tween_property(player_pivot, "scale", Vector2(0.8, 0.8), 0.2)
		tw.tween_property(player_pivot, "scale", Vector2(1.0, 1.0), 0.2)

	hud.update_level_info(level.name)
	hud.update_step_count(current_steps, level.step_limit)
	hud.update_password_display()
	hud.update_difficulty_display(level)
	if not game_state.is_password_mode:
		save_manager.current_level = level_id
		save_manager.save_game()
	hud.hide_overlays()
	call_deferred("_update_push_preview")
	call_deferred("_update_reachability_preview")

func _clear_board():
	if player_node:
		player_node.queue_free()
		player_node = null
	_push_previews.clear()
	_reach_previews.clear()
	_current_push_dests.clear()
	_current_dot_positions.clear()
	_pushable_boxes.clear()
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
	fg.color = Color("#000000")
	floor_container.add_child(fg)

	for row in level.rows:
		for col in level.cols:
			if grid_state[row][col] == CELL.WALL:
				var w = Sprite2D.new()
				w.texture = ATLAS_TEX
				w.region_enabled = true
				w.region_rect = Rect2(0, 0, 64, 64)
				w.scale = Vector2(tile_size / 64.0, tile_size / 64.0)
				w.position = board_offset + Vector2(col * tile_size + tile_size / 2, row * tile_size + tile_size / 2)
				wall_container.add_child(w)

	for t in targets:
		var m = Sprite2D.new()
		m.texture = ATLAS_TEX
		m.region_enabled = true
		m.region_rect = Rect2(216, 0, 64, 64)
		m.scale = Vector2(tile_size / 64.0, tile_size / 64.0)
		m.position = board_offset + Vector2(t.x * tile_size + tile_size / 2, t.y * tile_size + tile_size / 2)
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

	# Pivot node — rotates the whole unit around tile center
	var pivot = Node2D.new()
	pivot.name = "Pivot"

	# Player sprite
	var body = Sprite2D.new()
	body.texture = PLAYER_TEX
	body.scale = Vector2(tile_size / 64.0, tile_size / 64.0)
	_player_body = body
	pivot.add_child(body)

	player_pivot = pivot

	player_node.add_child(pivot)
	entity_container.add_child(player_node)

func _make_box(col: int, row: int):
	var b = Area2D.new()
	b.position = _grid_to_pixel(col, row)

	var vis = Sprite2D.new()
	vis.texture = ATLAS_TEX
	vis.region_enabled = true
	vis.region_rect = Rect2(64, 0, 64, 64)
	vis.scale = Vector2(tile_size / 64.0, tile_size / 64.0)
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
		_movement_timer = 1.0
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
		_movement_timer = 1.0
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
	_update_push_preview()
	_update_reachability_preview()
	hud.update_step_count(current_steps, level.step_limit)

func _update_box_visuals():
	for i in boxes.size():
		var on_target = box_positions[i] in targets
		boxes[i].is_on_target = on_target

func _update_player_color():
	if not _player_body or level.is_empty():
		return
	var ratio = float(max(0, level.step_limit - current_steps)) / level.step_limit
	_player_body.self_modulate = Color.WHITE.lerp(Color("#888888"), 1.0 - ratio)

func _update_push_preview():
	if game_over:
		return

	_current_push_dests.clear()
	var dirs = [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]

	# Reset old pushable boxes
	var prev_pushable = _pushable_boxes.duplicate()
	_pushable_boxes.clear()

	var idx := 0
	for dir in dirs:
		var box_cell = player_pos + dir
		var dest_cell = box_cell + dir
		var bx = int(box_cell.x)
		var by = int(box_cell.y)
		var dx = int(dest_cell.x)
		var dy = int(dest_cell.y)

		if bx < 0 or bx >= level.cols or by < 0 or by >= level.rows:
			continue
		if dx < 0 or dx >= level.cols or dy < 0 or dy >= level.rows:
			continue
		if _get_box_at(box_cell) < 0 or _get_box_at(dest_cell) >= 0 or grid_state[dy][dx] != CELL.FLOOR:
			continue

		# Track this box as pushable (for pulsing animation)
		var bi = _get_box_at(box_cell)
		if bi >= 0:
			_pushable_boxes.append(bi)

		# Get or create push arrow preview
		if idx >= _push_previews.size():
			var p = Polygon2D.new()
			p.color = Color("#60d030", 0.35)
			entity_container.add_child(p)
			_push_previews.append(p)
		var p = _push_previews[idx]
		_current_push_dests[dest_cell] = dir
		p.polygon = _make_push_arrow(dir)
		p.position = _grid_to_pixel(dx, dy)
		p.show()
		idx += 1

	# Hide unused previews
	while idx < _push_previews.size():
		_push_previews[idx].hide()
		idx += 1

	# Reset boxes that are no longer pushable
	for bi in prev_pushable:
		if not bi in _pushable_boxes and bi < boxes.size():
			boxes[bi].scale = Vector2.ONE

func _make_push_arrow(dir: Vector2) -> PackedVector2Array:
	var h = tile_size * 0.4
	var w = tile_size * 0.25

	if dir == Vector2.RIGHT:
		return PackedVector2Array([
			Vector2(-tile_size / 2, -h),
			Vector2(-tile_size / 2, h),
			Vector2(w, 0),
		])
	elif dir == Vector2.LEFT:
		return PackedVector2Array([
			Vector2(tile_size / 2, -h),
			Vector2(tile_size / 2, h),
			Vector2(-w, 0),
		])
	elif dir == Vector2.UP:
		return PackedVector2Array([
			Vector2(-h, tile_size / 2),
			Vector2(h, tile_size / 2),
			Vector2(0, -w),
		])
	elif dir == Vector2.DOWN:
		return PackedVector2Array([
			Vector2(-h, -tile_size / 2),
			Vector2(h, -tile_size / 2),
			Vector2(0, w),
		])
	return PackedVector2Array()

func _update_reachability_preview():
	if game_over or level.is_empty():
		return

	# BFS from player_pos through floor cells, avoiding boxes and walls
	var reachable = {}
	var queue = [player_pos]
	reachable[player_pos] = true
	while queue.size() > 0:
		var current = queue.pop_front()
		for dir in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
			var next_cell = current + dir
			var nx = int(next_cell.x)
			var ny = int(next_cell.y)
			if nx < 0 or nx >= level.cols or ny < 0 or ny >= level.rows:
				continue
			if grid_state[ny][nx] == CELL.WALL:
				continue
			if next_cell in reachable:
				continue
			# Boxes block movement
			var blocked = false
			for bp in box_positions:
				if bp == next_cell:
					blocked = true
					break
			if blocked:
				continue
			reachable[next_cell] = true
			queue.append(next_cell)

	# Find valid stand positions: reachable floor cells adjacent to boxes
	var stand_positions = {}
	for bp in box_positions:
		for dir in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
			var sp = bp + dir
			if sp == player_pos:
				continue
			var sx = int(sp.x)
			var sy = int(sp.y)
			if sx < 0 or sx >= level.cols or sy < 0 or sy >= level.rows:
				continue
			if grid_state[sy][sx] == CELL.WALL:
				continue
			# Cell occupied by another box
			var occupied = false
			for obp in box_positions:
				if obp == sp:
					occupied = true
					break
			if occupied:
				continue
			if reachable.has(sp):
				stand_positions[sp] = true

	_current_dot_positions = stand_positions.duplicate()
	# Show/hide reachability previews
	var idx := 0
	for pos in stand_positions.keys():
		if idx >= _reach_previews.size():
			var p = preload("res://scripts/game/reach_dot.gd").new()
			p.tile_size = tile_size
			entity_container.add_child(p)
			_reach_previews.append(p)
		var p = _reach_previews[idx]
		p.position = _grid_to_pixel(pos.x, pos.y)
		p.show()
		idx += 1

	while idx < _reach_previews.size():
		_reach_previews[idx].hide()
		idx += 1

func _find_path(from_pos: Vector2, to_pos: Vector2) -> Array:
	if from_pos == to_pos:
		return [from_pos]

	var came_from = {}
	var queue = [from_pos]
	came_from[from_pos] = null

	while queue.size() > 0:
		var current = queue.pop_front()
		if current == to_pos:
			var path = []
			var node = to_pos
			while node != null:
				path.append(node)
				node = came_from.get(node)
			path.reverse()
			return path

		for dir in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
			var next_cell = current + dir
			var nx = int(next_cell.x)
			var ny = int(next_cell.y)
			if nx < 0 or nx >= level.cols or ny < 0 or ny >= level.rows:
				continue
			if grid_state[ny][nx] == CELL.WALL:
				continue
			if came_from.has(next_cell):
				continue
			# Boxes block movement
			var blocked = false
			for bp in box_positions:
				if bp == next_cell:
					blocked = true
					break
			if blocked:
				continue
			came_from[next_cell] = current
			queue.append(next_cell)

	return []

func _walk_to(target: Vector2):
	var path = _find_path(player_pos, target)
	if path.is_empty() or path.size() < 2:
		return
	_walk_path(path)

func _walk_path(path: Array):
	_is_auto_walking = true
	for i in range(1, path.size()):
		if game_over:
			break
		var dir = path[i] - path[i-1]
		move_player(dir)
		await player_moved
	_is_auto_walking = false

func _check_game_state():
	var won = true
	for t in targets:
		if t not in box_positions:
			won = false
			break

	if won:
		game_over = true
		game_state.level_completed(level.id, current_steps)
		await get_tree().create_timer(0.5).timeout
		_go_to_next_dialogue()
		return

	if current_steps > level.step_limit:
		game_over = true
		hud.show_defeat()

func _on_tween_done():
	is_moving = false
	_update_push_preview()
	_update_reachability_preview()
	player_moved.emit()

func _go_to_next_dialogue():
	var next_id = game_state.current_level_id + 1
	if game_state.is_password_mode:
		game_state.is_password_mode = false
		get_tree().change_scene_to_file("res://scenes/main.tscn")
		return
	var story = story_data.get_story(game_state.current_level_id)
	if not story.is_empty():
		game_state.pending_story = story
		game_state.next_level_after_dialogue = next_id
		get_tree().change_scene_to_file("res://scenes/dialogue.tscn")
	else:
		if next_id <= level_data.get_level_count():
			start_level(next_id)

func restart_level():
	start_level(level.id)
