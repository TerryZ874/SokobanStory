extends Control

func _ready():
	$Title.add_theme_font_size_override("font_size", 64)
	$VersionLabel.add_theme_color_override("font_color", Color("#808080"))
	$StartBtn.pressed.connect(_on_start)
	$SandboxBtn.pressed.connect(_on_sandbox)
	$PasswordBtn.pressed.connect(_on_password_btn)
	$QuitBtn.pressed.connect(_on_quit)
	$PasswordPanel/ConfirmBtn.pressed.connect(_on_password_confirm)
	$PasswordPanel/CancelBtn.pressed.connect(_on_password_cancel)

func _on_start():
	game_state.is_sandbox = false
	game_state.current_level_id = 1
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_sandbox():
	game_state.is_sandbox = true
	game_state.current_level_id = 101
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_quit():
	get_tree().quit()

func _on_password_btn():
	$PasswordPanel.show()
	$PasswordPanel/LineEdit.clear()
	$PasswordPanel/ErrorLabel.text = ""
	$PasswordPanel/LineEdit.grab_focus()

func _on_password_cancel():
	$PasswordPanel.hide()

func _on_password_confirm():
	var pwd = $PasswordPanel/LineEdit.text
	var lid = game_state.validate_password(pwd)
	if lid > 0:
		$PasswordPanel.hide()
		game_state.is_sandbox = false
		game_state.current_level_id = lid
		get_tree().change_scene_to_file("res://scenes/game.tscn")
	else:
		$PasswordPanel/ErrorLabel.text = "密码无效，请重新输入"

func _input(event):
	if $PasswordPanel.visible and event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ENTER or event.keycode == KEY_KP_ENTER:
			_on_password_confirm()
		elif event.keycode == KEY_ESCAPE:
			_on_password_cancel()
