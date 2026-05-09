extends Control

@onready var level_label = $LevelLabel
@onready var step_label = $StepLabel
@onready var victory_panel = $VictoryPanel
@onready var defeat_panel = $DefeatPanel
@onready var victory_next_btn = $VictoryPanel/NextBtn
@onready var victory_replay_btn = $VictoryPanel/ReplayBtn
@onready var defeat_retry_btn = $DefeatPanel/RetryBtn
@onready var password_label = $VictoryPanel/PasswordLabel

func _ready():
	hide_overlays()

	$UndoBtn.pressed.connect(_on_undo)
	$RestartBtn.pressed.connect(_on_restart)
	$BackBtn.pressed.connect(_on_back)
	victory_next_btn.pressed.connect(_on_next_level)
	victory_replay_btn.pressed.connect(_on_restart)
	$VictoryPanel/BackBtn.pressed.connect(_on_back)
	defeat_retry_btn.pressed.connect(_on_restart)
	$DefeatPanel/BackBtn.pressed.connect(_on_back)

	victory_next_btn.add_theme_color_override("font_color", Color("#33ff33"))

func update_level_info(name: String):
	level_label.text = name

func update_password_display():
	if game_state.is_sandbox:
		$PasswordHint.hide()
		return
	var pwd = game_state.generate_password(game_state.current_level_id)
	$PasswordHint.text = "密码: " + pwd
	$PasswordHint.show()

func update_step_count(steps: int, max_steps: int):
	var color = Color("#ffffff")
	if steps > max_steps:
		color = Color("#ff4444")
	step_label.text = "步数: " + str(steps) + " / " + str(max_steps)
	step_label.add_theme_color_override("font_color", color)

func show_victory():
	victory_panel.show()
	if not game_state.is_sandbox:
		var pwd = game_state.generate_password(game_state.current_level_id)
		password_label.text = "密码: " + pwd
		password_label.show()
	else:
		password_label.hide()

	var next_id = game_state.current_level_id + 1
	if game_state.is_sandbox:
		var has_next_sandbox = not sandbox_data.get_level(next_id).is_empty()
		victory_next_btn.disabled = not has_next_sandbox
	else:
		var has_next = next_id <= level_data.get_level_count()
		var has_story = not story_data.get_story(game_state.current_level_id).is_empty()
		victory_next_btn.disabled = not has_next and not has_story

func show_defeat():
	defeat_panel.show()

func hide_overlays():
	victory_panel.hide()
	defeat_panel.hide()

func get_board():
	return get_parent().get_parent()

func _on_undo():
	get_board().undo()

func _on_restart():
	hide_overlays()
	get_board().restart_level()

func _on_back():
	get_tree().change_scene_to_file("res://scenes/main.tscn")

func _on_next_level():
	var next_id = game_state.current_level_id + 1
	hide_overlays()
	if game_state.is_sandbox:
		if not sandbox_data.get_level(next_id).is_empty():
			get_board().start_level(next_id)
		return
	var story = story_data.get_story(game_state.current_level_id)
	if not story.is_empty():
		game_state.pending_story = story
		game_state.next_level_after_dialogue = next_id
		get_tree().change_scene_to_file("res://scenes/dialogue.tscn")
	else:
		if next_id <= level_data.get_level_count():
			get_board().start_level(next_id)
