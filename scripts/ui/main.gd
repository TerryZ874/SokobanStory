extends Control

func _ready():
	$Title.add_theme_font_size_override("font_size", 64)
	$StartBtn.pressed.connect(_on_start)
	$QuitBtn.pressed.connect(_on_quit)

func _on_start():
	game_state.current_level_id = 1
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_quit():
	get_tree().quit()
