extends Control

var dialogue_lines: Array = []
var current_index := 0
var skip_pressed := false
var showing := false
var advancing := false

@onready var message_list = $Scroll/MessageList
@onready var scroll = $Scroll
@onready var skip_btn = $SkipBtn
@onready var continue_btn = $ContinueBtn

const BLIP = preload("res://audio/sfx_message.mp3")
var _blip_player: AudioStreamPlayer

const SPEAKER_COLORS := {
	"c01": Color("#4a9eff"),
	"c02": Color("#4ecdc4"),
	"c03": Color("#ff6b6b"),
	"c04": Color("#ffa94d"),
	"c05": Color("#ffd43b"),
}

const BUBBLE_COLORS := {
	"c01": Color(0.29, 0.62, 1.0, 0.3),
	"c02": Color(0.31, 0.80, 0.77, 0.15),
	"c04": Color(1.0, 0.66, 0.30, 0.15),
	"c05": Color(1.0, 0.83, 0.23, 0.15),
}

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
	continue_btn.add_theme_color_override("font_color", Color("#33ff33"))

	_start_show_messages()


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

	# Wait two frames for layout to settle, then scroll to bottom
	await get_tree().process_frame
	await get_tree().process_frame
	scroll.scroll_vertical = int(scroll.get_v_scroll_bar().max_value)

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
	scroll.scroll_vertical = int(scroll.get_v_scroll_bar().max_value)

	showing = false
	continue_btn.show()
	advancing = false


func _add_message(line: Dictionary):
	_blip_player.play()

	var is_player = line.speaker == PLAYER_ID
	var char_data = story_data.get_character(line.speaker)
	var char_name = char_data.get("name", line.speaker) if not char_data.is_empty() else line.speaker
	var color = SPEAKER_COLORS.get(line.speaker, Color("#808080"))

	var row = HBoxContainer.new()
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var spacer = Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var content = VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_SHRINK_CENTER

	# Header: avatar + name
	var header = HBoxContainer.new()

	var avatar = Label.new()
	avatar.text = char_name.left(1)
	avatar.add_theme_color_override("font_color", Color.WHITE)
	avatar.add_theme_font_size_override("font_size", 28)
	avatar.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	avatar.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	avatar.custom_minimum_size = Vector2(64, 64)

	var avatar_bg = StyleBoxFlat.new()
	avatar_bg.bg_color = color
	avatar_bg.corner_radius_top_left = 16
	avatar_bg.corner_radius_top_right = 16
	avatar_bg.corner_radius_bottom_left = 16
	avatar_bg.corner_radius_bottom_right = 16
	avatar.add_theme_stylebox_override("normal", avatar_bg)

	var name_label = Label.new()
	name_label.text = char_name
	name_label.add_theme_color_override("font_color", color)
	name_label.add_theme_font_size_override("font_size", 28)

	if is_player:
		header.add_child(name_label)
		header.add_child(avatar)
		header.alignment = BoxContainer.ALIGNMENT_END
	else:
		header.add_child(avatar)
		header.add_child(name_label)

	content.add_child(header)

	# Text bubble
	var bubble = Label.new()
	bubble.text = line.text
	bubble.add_theme_color_override("font_color", Color.WHITE)
	bubble.add_theme_font_size_override("font_size", 36)
	bubble.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bubble.custom_minimum_size = Vector2(700, 0)

	var bubble_bg = StyleBoxFlat.new()
	bubble_bg.bg_color = BUBBLE_COLORS.get(line.speaker, Color(0.2, 0.2, 0.2, 0.3))
	bubble_bg.corner_radius_top_left = 12
	bubble_bg.corner_radius_top_right = 12
	bubble_bg.corner_radius_bottom_left = 12
	bubble_bg.corner_radius_bottom_right = 12
	bubble_bg.set_content_margin_all(12)
	bubble.add_theme_stylebox_override("normal", bubble_bg)

	content.add_child(bubble)

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


func _input(event):
	if not showing or advancing:
		return

	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if skip_btn.get_global_rect().has_point(event.global_position):
			return
		if continue_btn.visible and continue_btn.get_global_rect().has_point(event.global_position):
			return
		_show_next_message()

	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_SPACE, KEY_ENTER:
				_show_next_message()
			KEY_ESCAPE:
				_on_skip()


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
