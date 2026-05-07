extends Control

@onready var level_label = $LevelLabel
@onready var step_label = $StepLabel
@onready var victory_panel = $VictoryPanel
@onready var defeat_panel = $DefeatPanel
@onready var victory_next_btn = $VictoryPanel/NextBtn
@onready var defeat_retry_btn = $DefeatPanel/RetryBtn

func _ready():
	hide_overlays()

	$UndoBtn.pressed.connect(_on_undo)
	$RestartBtn.pressed.connect(_on_restart)
	$BackBtn.pressed.connect(_on_back)
	victory_next_btn.pressed.connect(_on_next_level)
	$VictoryPanel/BackBtn.pressed.connect(_on_back)
	defeat_retry_btn.pressed.connect(_on_restart)
	$DefeatPanel/BackBtn.pressed.connect(_on_back)

func update_level_info(name: String):
	level_label.text = name

func update_step_count(steps: int, max_steps: int):
	var color = Color("#ffffff")
	if steps > max_steps:
		color = Color("#ff4444")
	step_label.text = "步数: " + str(steps) + " / " + str(max_steps)
	step_label.add_theme_color_override("font_color", color)

func show_victory():
	victory_panel.show()
	var next_id = game_state.current_level_id + 1
	victory_next_btn.disabled = next_id > level_data.get_level_count()

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
	if next_id <= level_data.get_level_count():
		hide_overlays()
		get_board().start_level(next_id)
