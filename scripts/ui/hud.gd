extends Control

@onready var level_label = $LevelLabel
@onready var step_label = $StepLabel
@onready var victory_panel = $VictoryPanel
@onready var defeat_panel = $DefeatPanel
@onready var victory_next_btn = $VictoryPanel/NextBtn
@onready var victory_replay_btn = $VictoryPanel/ReplayBtn
@onready var defeat_retry_btn = $DefeatPanel/RetryBtn
@onready var password_label = $VictoryPanel/PasswordLabel
@onready var ai_difficulty_label = $AIDifficultyLabel
@onready var player_difficulty_label = $PlayerDifficultyLabel

var _rating_buttons: Array[Button] = []
var _rating_panel: Control = null
var _rating_visible := false

func _ready():
	hide_overlays()
	_setup_rating_panel()

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
		ai_difficulty_label.hide()
		player_difficulty_label.hide()
		return
	var pwd = game_state.generate_password(game_state.current_level_id)
	$PasswordHint.text = "密码: " + pwd
	$PasswordHint.show()
	ai_difficulty_label.show()
	player_difficulty_label.show()

func _setup_rating_panel():
	player_difficulty_label.mouse_filter = Control.MOUSE_FILTER_STOP
	player_difficulty_label.gui_input.connect(_on_player_label_click)

	_rating_panel = HBoxContainer.new()
	_rating_panel.name = "RatingPanel"
	_rating_panel.position = Vector2(20, 245)
	_rating_panel.hide()
	add_child(_rating_panel)

	for i in range(1, 11):
		var btn = Button.new()
		btn.text = str(i)
		btn.custom_minimum_size = Vector2(30, 28)
		btn.add_theme_font_size_override("font_size", 16)
		var score = i
		btn.pressed.connect(func(): _on_rating_selected(score))
		_rating_panel.add_child(btn)
		_rating_buttons.append(btn)

func _on_player_label_click(event: InputEvent):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_rating_visible = not _rating_visible
		_rating_panel.visible = _rating_visible

func _on_rating_selected(score: int):
	var lid = game_state.current_level_id
	save_manager.set_player_difficulty(lid, score)
	_rating_visible = false
	_rating_panel.hide()
	_reload_level()
	player_difficulty_label.text = "玩家难度: " + str(score) + " / 10"

func _reload_level():
	var board = get_board()
	if board:
		var lv = board.level
		if lv:
			update_difficulty_display(lv)

func update_difficulty_display(level: Dictionary):
	if game_state.is_sandbox:
		return
	var ai_score = level.get("ai_difficulty", 0.0)
	var player_score = save_manager.get_player_difficulty(game_state.current_level_id)
	ai_difficulty_label.text = "AI难度: " + str(ai_score) + " / 10"
	if player_score > 0:
		player_difficulty_label.text = "玩家难度: " + str(player_score) + " / 10"
	else:
		player_difficulty_label.text = "玩家难度: ? / 10"

func update_step_count(steps: int, max_steps: int):
	var remaining = max_steps - steps
	var color = Color("#ffffff")
	if steps > max_steps or remaining < 2:
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
