extends Control

const THUMB_SIZE := 200
const CELL_GAP := 10

@onready var grid = $ScrollContainer/Grid

func _ready():
	$BackBtn.pressed.connect(_on_back)

	var count = level_data.get_level_count()
	for lid in range(1, count + 1):
		var level = level_data.get_level(lid)
		if level.is_empty():
			continue
		_add_cell(level)


func _add_cell(level: Dictionary):
	var lid = level.id
	var completed = save_manager.get_level_steps(lid) > 0
	var cell = VBoxContainer.new()
	cell.custom_minimum_size = Vector2(280, 340)
	cell.size_flags_horizontal = Control.SIZE_SHRINK_CENTER

	# Name
	var name_label = Label.new()
	name_label.text = level.name
	name_label.add_theme_font_size_override("font_size", 24)
	name_label.add_theme_color_override("font_color", Color("#cccccc"))
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	name_label.custom_minimum_size = Vector2(0, 40)
	cell.add_child(name_label)

	# Thumbnail
	var thumb = ColorRect.new()
	thumb.custom_minimum_size = Vector2(THUMB_SIZE, THUMB_SIZE)
	thumb.size = Vector2(THUMB_SIZE, THUMB_SIZE)
	thumb.color = Color(0.15, 0.15, 0.17, 1)
	thumb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cell.add_child(thumb)

	if completed:
		_render_thumbnail(thumb, level)
	else:
		var q = Label.new()
		q.text = "?"
		q.add_theme_font_size_override("font_size", 96)
		q.add_theme_color_override("font_color", Color("#555555"))
		q.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		q.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		q.size = Vector2(THUMB_SIZE, THUMB_SIZE)
		q.mouse_filter = Control.MOUSE_FILTER_IGNORE
		thumb.add_child(q)

	# Steps
	var steps_label = Label.new()
	var steps = save_manager.get_level_steps(lid)
	if steps > 0:
		steps_label.text = "步数: %d" % steps
	else:
		steps_label.text = "步数: 未知"
	steps_label.add_theme_font_size_override("font_size", 20)
	steps_label.add_theme_color_override("font_color", Color("#999999"))
	steps_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	steps_label.custom_minimum_size = Vector2(0, 30)
	cell.add_child(steps_label)

	# Password
	var pwd_label = Label.new()
	if completed:
		pwd_label.text = "密码: " + game_state.generate_password(lid)
	else:
		pwd_label.text = "密码: 未知"
	pwd_label.add_theme_font_size_override("font_size", 20)
	pwd_label.add_theme_color_override("font_color", Color("#666666"))
	pwd_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pwd_label.custom_minimum_size = Vector2(0, 30)
	cell.add_child(pwd_label)

	# Click to copy password (completed levels only)
	if completed:
		var pwd = game_state.generate_password(lid)
		cell.mouse_filter = Control.MOUSE_FILTER_STOP
		cell.gui_input.connect(func(event: InputEvent):
			if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
				DisplayServer.clipboard_set(pwd)
				_show_floating_text("关卡密码已复制")
		)

	grid.add_child(cell)


func _show_floating_text(text: String):
	var label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 28)
	label.add_theme_color_override("font_color", Color("#33ff33"))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var mouse_pos = get_local_mouse_position()
	label.position = Vector2(mouse_pos.x - 110, mouse_pos.y - 50)
	label.size = Vector2(220, 40)
	add_child(label)

	var tw = create_tween().set_parallel()
	tw.tween_property(label, "position:y", label.position.y - 80, 2.8).set_ease(Tween.EASE_OUT)
	tw.tween_property(label, "modulate:a", 0.0, 2.8).set_ease(Tween.EASE_IN)
	tw.finished.connect(label.queue_free)


func _render_thumbnail(container: ColorRect, level: Dictionary):
	var cols = level.cols
	var rows = level.rows
	var tile = mini(THUMB_SIZE / cols, THUMB_SIZE / rows)
	var offset_x = (THUMB_SIZE - cols * tile) / 2
	var offset_y = (THUMB_SIZE - rows * tile) / 2

	# Collect target positions
	var target_set = {}
	for t in level.targets:
		target_set[Vector2i(t[0], t[1])] = true

	# Draw grid
	for row in rows:
		for col in cols:
			var cell_type = level.grid[row][col]
			var tx = offset_x + col * tile
			var ty = offset_y + row * tile

			var rect = ColorRect.new()
			rect.size = Vector2(tile, tile)
			rect.position = Vector2(tx, ty)
			rect.mouse_filter = Control.MOUSE_FILTER_IGNORE

			if cell_type == 1:
				rect.color = Color("#777777")
			elif cell_type == 2:
				rect.color = Color("#d4a574")
			elif target_set.has(Vector2i(col, row)):
				rect.color = Color("#ff6b6b")
			else:
				rect.color = Color("#252525")

			container.add_child(rect)

	# Draw target markers on top of boxes or empty floor
	for t in level.targets:
		var tx = offset_x + t[0] * tile
		var ty = offset_y + t[1] * tile
		var dot = ColorRect.new()
		var dot_s = tile * 0.4
		dot.size = Vector2(dot_s, dot_s)
		dot.position = Vector2(tx + (tile - dot_s) * 0.5, ty + (tile - dot_s) * 0.5)
		dot.color = Color("#ff4444")
		dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
		container.add_child(dot)


func _on_back():
	get_tree().change_scene_to_file("res://scenes/main.tscn")
