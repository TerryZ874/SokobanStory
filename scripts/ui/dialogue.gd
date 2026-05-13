extends Control

var dialogue_lines: Array = []
var current_index := 0
var skip_pressed := false
var showing := false
var advancing := false
var _text_revealing := false
var _text_tween: Tween = null
var _current_bubble: Label = null
var _current_fultext: String = ""
var _full_text: String = ""
var _reveal_count: float = 0.0
var _scramble_accum: float = 0.0

@onready var message_list = $Scroll/MessageList
@onready var scroll = $Scroll
@onready var skip_btn = $SkipBtn
@onready var continue_btn = $ContinueBtn

const BLIP = preload("res://audio/sfx_message.mp3")
var _blip_player: AudioStreamPlayer
const GREEN := Color("#60d030")
const PLAYER_ID := "c01"

func _ready():
	dialogue_lines = game_state.pending_story
	if dialogue_lines.is_empty():
		_finish_dialogue()
		return

	_blip_player = AudioStreamPlayer.new()
	_blip_player.stream = BLIP
	add_child(_blip_player)

	skip_btn.pressed.connect(_on_skip)
	continue_btn.pressed.connect(_on_continue)
	continue_btn.hide()
	continue_btn.add_theme_font_size_override("font_size", 32)
	continue_btn.add_theme_color_override("font_color", GREEN)
	skip_btn.add_theme_color_override("font_color", GREEN)
	skip_btn.add_theme_font_size_override("font_size", 28)

	_start_show_messages()


func _process(delta):
	if not _text_revealing or _current_bubble == null:
		return

	# Update scramble display every 0.1s
	_scramble_accum += delta
	if _scramble_accum >= 0.1:
		_scramble_accum = 0.0
		_update_scramble_text()


func _start_show_messages():
	showing = true
	current_index = 0
	_show_next_message()


func _show_next_message():
	if advancing:
		return
	advancing = true

	if skip_pressed:
		_show_all_remaining()
		return

	if current_index >= dialogue_lines.size():
		showing = false
		continue_btn.show()
		advancing = false
		return

	var line = dialogue_lines[current_index]
	_add_message(line)
	current_index += 1

	# Wait for layout to settle, then scroll to bottom
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	# Lock bubble height so scramble text doesn't affect layout
	if _current_bubble != null:
		_current_bubble.custom_minimum_size = Vector2(700, _current_bubble.size.y)
	_scroll_last_message_bottom()

	advancing = false

	if current_index >= dialogue_lines.size():
		showing = false
		continue_btn.show()


func _show_all_remaining():
	while current_index < dialogue_lines.size():
		var line = dialogue_lines[current_index]
		_add_message(line)
		current_index += 1

	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	# Lock all bubble heights so scramble text doesn't affect layout
	for j in range(message_list.get_child_count()):
		var row = message_list.get_child(j)
		if not row is HBoxContainer:
			continue
		for k in range(row.get_child_count()):
			var col = row.get_child(k)
			if col is VBoxContainer:
				for m in range(col.get_child_count()):
					var bubble = col.get_child(m)
					if bubble is Label and bubble.size.y > 0:
						bubble.custom_minimum_size = bubble.size
	_scroll_last_message_bottom()

	showing = false
	continue_btn.show()
	advancing = false


func _add_message(line: Dictionary):
	_blip_player.play()

	var is_player = line.speaker == PLAYER_ID
	var char_data = story_data.get_character(line.speaker)
	var char_name = char_data.get("name", line.speaker) if not char_data.is_empty() else line.speaker

	var row = HBoxContainer.new()
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var spacer = Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var content = VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_SHRINK_CENTER

	# Header: name only (no avatar). Player name is hidden.
	if not is_player:
		var header = HBoxContainer.new()
		var name_label = Label.new()
		name_label.text = char_name
		name_label.add_theme_color_override("font_color", GREEN)
		name_label.add_theme_font_size_override("font_size", 28)
		header.add_child(name_label)
		content.add_child(header)

	# Text bubble
	var bubble = Label.new()
	_current_fultext = line.text
	_full_text = line.text
	bubble.text = _full_text
	bubble.add_theme_color_override("font_color", Color.WHITE)
	bubble.add_theme_font_size_override("font_size", 36)
	bubble.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bubble.custom_minimum_size = Vector2(700, 0)

	var bubble_bg = StyleBoxFlat.new()
	if is_player:
		# Player: dark green background, no border
		bubble_bg.bg_color = Color("#003300")
		bubble_bg.set_content_margin_all(12)
	else:
		# Others: black background, green border
		bubble_bg.bg_color = Color("#000000")
		bubble_bg.border_color = GREEN
		bubble_bg.border_width_top = 2
		bubble_bg.border_width_bottom = 2
		bubble_bg.border_width_left = 2
		bubble_bg.border_width_right = 2
		bubble_bg.set_content_margin_all(12)
	bubble.add_theme_stylebox_override("normal", bubble_bg)

	content.add_child(bubble)

	# Start scramble reveal animation
	_current_bubble = bubble
	_text_revealing = true
	_reveal_count = 0.0
	_scramble_accum = 0.0
	if _text_tween:
		_text_tween.kill()
	# Use tween_method to advance reveal count
	_text_tween = create_tween()
	_text_tween.set_process_mode(Tween.TWEEN_PROCESS_IDLE)
	_text_tween.tween_method(
		func(v): _reveal_count = v,
		0.0,
		float(_full_text.length()),
		max(0.5, _full_text.length() * 0.033)
	)
	_text_tween.finished.connect(func():
		_text_revealing = false
		_text_tween = null
		# Show final clean text
		if _current_bubble:
			_current_bubble.text = _full_text
	)

	if is_player:
		row.add_child(spacer)
		row.add_child(content)
	else:
		row.add_child(content)
		row.add_child(spacer)

	message_list.add_child(row)

	var msg_spacer = Control.new()
	msg_spacer.custom_minimum_size = Vector2(0, 8)
	message_list.add_child(msg_spacer)


func _scroll_last_message_bottom():
	# Keep scrolling down until position stabilizes (layout fully settled)
	for _i in 10:
		var prev = scroll.scroll_vertical
		scroll.scroll_vertical = 999999
		await get_tree().process_frame
		if scroll.scroll_vertical == prev:
			break


func _update_scramble_text():
	if _current_bubble == null or _full_text.is_empty():
		return
	var rc = int(_reveal_count)
	var result = ""
	for i in range(_full_text.length()):
		if i < rc:
			result += _full_text[i]
		else:
			result += char(randi_range(33, 126))
	_current_bubble.text = result


func _input(event):
	if not showing:
		return

	var click := false
	var skip_key := false
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if skip_btn.get_global_rect().has_point(event.global_position):
			return
		if continue_btn.visible and continue_btn.get_global_rect().has_point(event.global_position):
			return
		click = true
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_SPACE, KEY_ENTER:
				skip_key = true
			KEY_ESCAPE:
				_on_skip()
				return

	if not (click or skip_key):
		return

	# If text is still revealing, skip animation but don't advance
	if _text_revealing:
		_skip_text_reveal()
		return

	if advancing:
		return

	_show_next_message()


func _skip_text_reveal():
	if _text_tween:
		_text_tween.kill()
		_text_tween = null
	_text_revealing = false
	if _current_bubble:
		_current_bubble.text = _full_text


func _on_skip():
	if not showing:
		return
	skip_pressed = true
	if not advancing:
		_show_all_remaining()


func _on_continue():
	_finish_dialogue()


func _finish_dialogue():
	game_state.pending_story = []
	var next_level = game_state.next_level_after_dialogue
	if next_level <= level_data.get_level_count():
		game_state.current_level_id = next_level
		get_tree().change_scene_to_file("res://scenes/game.tscn")
		return

	var epilogue = story_data.get_story(next_level)
	if not epilogue.is_empty():
		game_state.pending_story = epilogue
		game_state.next_level_after_dialogue = next_level + 1
		get_tree().change_scene_to_file("res://scenes/dialogue.tscn")
		return

	if save_manager.game_completed:
		get_tree().change_scene_to_file("res://scenes/game_complete.tscn")
	else:
		get_tree().change_scene_to_file("res://scenes/main.tscn")
