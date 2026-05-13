extends Control

@onready var level_label = $LevelLabel
@onready var step_label = $StepLabel
@onready var defeat_panel = $DefeatPanel
@onready var defeat_retry_btn = $DefeatPanel/RetryBtn
@onready var pause_panel = $PausePanel
@onready var ai_difficulty_label = $AIDifficultyLabel
@onready var player_difficulty_label = $PlayerDifficultyLabel

var _rating_buttons: Array[Button] = []
var _rating_panel: Control = null
var _rating_visible := false

func _ready():
	pause_panel.process_mode = Node.PROCESS_MODE_WHEN_PAUSED
	hide_overlays()
	_setup_rating_panel()

	$UndoBtn.focus_mode = Control.FOCUS_NONE
	$UndoBtn.pressed.connect(_on_undo)
	$RestartBtn.focus_mode = Control.FOCUS_NONE
	$RestartBtn.pressed.connect(_on_restart)
	defeat_retry_btn.pressed.connect(_on_restart)
	$DefeatPanel/BackBtn.pressed.connect(_on_back)

	pause_panel.hide()
	$PausePanel/ResumeBtn.pressed.connect(_on_resume)
	$PausePanel/RestartBtn.pressed.connect(_on_restart)
	$PausePanel/BackBtn.pressed.connect(_on_back)

func update_level_info(level_id: int):
	level_label.text = "// %04d关" % level_id

func update_password_display():
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
	var ai_score = level.get("ai_difficulty", 0.0)
	var player_score = save_manager.get_player_difficulty(game_state.current_level_id)
	ai_difficulty_label.text = "AI难度: " + str(ai_score) + " / 10"
	if player_score > 0:
		player_difficulty_label.text = "玩家难度: " + str(player_score) + " / 10"
	else:
		player_difficulty_label.text = "玩家难度: ? / 10"

func update_step_count(steps: int, max_steps: int):
	var remaining = max_steps - steps
	var color = Color("#60d030")
	if steps > max_steps or remaining < 2:
		color = Color("#ff4444")
	step_label.text = "步数: " + str(steps) + " / " + str(max_steps)
	step_label.add_theme_color_override("font_color", color)

func hide_overlays():
	defeat_panel.hide()

func show_defeat():
	defeat_panel.show()

func get_board():
	return get_parent().get_parent()

func _toggle_pause():
	if get_tree().paused:
		get_tree().paused = false
		pause_panel.hide()
	else:
		pause_panel.show()
		get_tree().paused = true

func _on_resume():
	get_tree().paused = false
	pause_panel.hide()

func _on_undo():
	get_board().undo()

func _on_restart():
	if get_tree().paused:
		get_tree().paused = false
		pause_panel.hide()
	hide_overlays()
	get_board().restart_level()

func _on_back():
	get_tree().paused = false
	get_tree().change_scene_to_file("res://scenes/main.tscn")
