extends Control

var dialogue_lines: Array = []
var current_index := 0
var advancing := false

@onready var name_label = $DialoguePanel/NameLabel
@onready var text_label = $DialoguePanel/TextLabel
@onready var ill_label = $DialoguePanel/IllustrationLabel
@onready var continue_hint = $DialoguePanel/ContinueHint

func _ready():
	dialogue_lines = game_state.pending_story
	if dialogue_lines.is_empty():
		_finish_dialogue()
		return

	$DialoguePanel/SkipBtn.pressed.connect(_on_skip)
	_show_line(0)

func _show_line(index: int):
	if index >= dialogue_lines.size():
		_finish_dialogue()
		return

	advancing = false
	var line = dialogue_lines[index]
	var char_data = story_data.get_character(line.speaker)
	var char_name = char_data.get("name", line.speaker) if not char_data.is_empty() else line.speaker

	name_label.text = char_name

	if line.has("illustration"):
		ill_label.text = "📷 " + line.illustration
		ill_label.show()
	else:
		ill_label.hide()

	text_label.text = line.text
	current_index = index
	continue_hint.text = "点击继续" if index < dialogue_lines.size() - 1 else "点击完成"

func _input(event):
	if advancing:
		return

	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if $DialoguePanel/SkipBtn.get_global_rect().has_point(event.global_position):
			return
		advancing = true
		_show_line(current_index + 1)

	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_SPACE, KEY_ENTER:
				advancing = true
				_show_line(current_index + 1)
			KEY_ESCAPE:
				_on_skip()

func _on_skip():
	_finish_dialogue()

func _finish_dialogue():
	game_state.pending_story = []
	var next_level = game_state.next_level_after_dialogue
	if next_level <= level_data.get_level_count():
		game_state.current_level_id = next_level
		get_tree().change_scene_to_file("res://scenes/game.tscn")
	else:
		get_tree().change_scene_to_file("res://scenes/main.tscn")
