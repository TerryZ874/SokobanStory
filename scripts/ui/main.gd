extends Control

const CITY = preload("res://scripts/ui/splash_city.gd")

var _all_lines: Array[String] = []

func _ready():
	var sf = SystemFont.new()
	sf.font_names = ["Menlo", "Courier New", "monospace"]
	$BgLabel.add_theme_font_override("font", sf)
	$BgLabel.add_theme_font_size_override("font_size", 20)
	$BgLabel.add_theme_color_override("font_color", Color(0.1, 0.9, 0.1))
	$BgLabel.add_theme_constant_override("line_spacing", -2)
	$BgLabel.mouse_filter = Control.MOUSE_FILTER_IGNORE

	$Title.add_theme_font_size_override("font_size", 84)
	$VersionLabel.add_theme_color_override("font_color", Color("#808080"))

	for b in [$ContinueBtn, $StartBtn, $AlbumBtn, $PasswordBtn, $QuitBtn]:
		b.add_theme_font_size_override("font_size", 34)

	# Continue button visibility
	if save_manager.has_save():
		save_manager.load_game()
		if save_manager.game_completed:
			$ContinueBtn.text = "继续游戏+"
		$ContinueBtn.show()
	else:
		$ContinueBtn.hide()

	# Album button visibility (show after at least 1 level completed)
	var any_completed = false
	for lid in range(1, level_data.get_level_count() + 1):
		if save_manager.get_level_steps(lid) > 0:
			any_completed = true
			break
	$AlbumBtn.visible = any_completed

	$ContinueBtn.pressed.connect(_on_continue)
	$StartBtn.pressed.connect(_on_start)
	$AlbumBtn.pressed.connect(_on_album)
	$PasswordBtn.pressed.connect(_on_password_btn)
	$QuitBtn.pressed.connect(_on_quit)
	$PasswordPanel/ConfirmBtn.pressed.connect(_on_password_confirm)
	$PasswordPanel/CancelBtn.pressed.connect(_on_password_cancel)
	$ConfirmPanel/ConfirmBtn.pressed.connect(_on_confirm_new_game)
	$ConfirmPanel/CancelBtn.pressed.connect(_on_cancel_new_game)

	_all_lines = _generate_bg_lines()
	_hide_menu()
	_animate_bg()

func _hide_menu():
	for child in get_children():
		if child == $BgLabel or child == $PasswordPanel or child == $ConfirmPanel:
			continue
		child.modulate = Color.TRANSPARENT

func _show_menu():
	var tw = create_tween().set_parallel(true)
	tw.set_trans(Tween.TRANS_CUBIC)
	for child in get_children():
		if child == $BgLabel or child == $PasswordPanel or child == $ConfirmPanel:
			continue
		tw.tween_property(child, "modulate", Color.WHITE, 0.25)

func _generate_bg_lines() -> Array[String]:
	var lines: Array[String] = []
	for line in CITY.CITYSCAPE.split("\n"):
		lines.append(line)
	return lines

func _animate_bg():
	var start_ms = Time.get_ticks_msec()
	var duration_ms = 1000
	var displayed = 0

	while displayed < _all_lines.size():
		var elapsed = Time.get_ticks_msec() - start_ms
		var target = mini(_all_lines.size(), int(elapsed * _all_lines.size() / duration_ms))
		target = maxi(target, 1)

		if target > displayed:
			$BgLabel.text = "\n".join(_all_lines.slice(0, target))
			displayed = target

		if displayed >= _all_lines.size():
			break

		await get_tree().process_frame

	$BgLabel.text = "\n".join(_all_lines)

	await get_tree().create_timer(0.15).timeout
	_show_menu()

func _on_start():
	if save_manager.has_save():
		$ConfirmPanel.show()
	else:
		_on_confirm_new_game()

func _on_continue():
	save_manager.load_game()
	game_state.current_level_id = save_manager.current_level
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_album():
	get_tree().change_scene_to_file("res://scenes/album.tscn")

func _on_confirm_new_game():
	save_manager.delete_save()
	game_state.current_level_id = 1
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_cancel_new_game():
	$ConfirmPanel.hide()

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
		game_state.is_password_mode = true
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
	if $ConfirmPanel.visible and event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			_on_cancel_new_game()
