extends Control

const SPLASH = preload("res://scripts/ui/splash_ascii.gd")

const BG_CHARS := "@%#*+=-:.~"
const BG_COLS := 320
const BG_ROWS := 90

const FACE_COLS := 120
const OFFSET_X := 100
const OFFSET_Y := 7

var _all_lines: Array[String] = []


func _ready():
	var sf = SystemFont.new()
	sf.font_names = ["Menlo", "Courier New", "monospace"]
	$BgLabel.add_theme_font_override("font", sf)
	$BgLabel.add_theme_font_size_override("font_size", 10)
	$BgLabel.add_theme_color_override("font_color", Color(0.35, 0.42, 0.35))
	$BgLabel.mouse_filter = Control.MOUSE_FILTER_IGNORE

	$Title.add_theme_font_size_override("font_size", 84)
	$VersionLabel.add_theme_color_override("font_color", Color("#808080"))

	for b in [$StartBtn, $PasswordBtn, $SandboxBtn, $QuitBtn]:
		b.add_theme_font_size_override("font_size", 34)

	$StartBtn.pressed.connect(_on_start)
	$SandboxBtn.pressed.connect(_on_sandbox)
	$PasswordBtn.pressed.connect(_on_password_btn)
	$QuitBtn.pressed.connect(_on_quit)
	$PasswordPanel/ConfirmBtn.pressed.connect(_on_password_confirm)
	$PasswordPanel/CancelBtn.pressed.connect(_on_password_cancel)

	_all_lines = _generate_bg_lines()
	_hide_menu()
	_animate_bg()


func _hide_menu():
	for child in get_children():
		if child == $BgLabel or child == $PasswordPanel:
			continue
		child.modulate = Color.TRANSPARENT


func _show_menu():
	var tw = create_tween().set_parallel(true)
	tw.set_trans(Tween.TRANS_CUBIC)
	for child in get_children():
		if child == $BgLabel or child == $PasswordPanel:
			continue
		tw.tween_property(child, "modulate", Color.WHITE, 0.25)


func _generate_bg_lines() -> Array[String]:
	var face_lines = SPLASH.SPLASH_ASCII.split("\n")
	var rng = RandomNumberGenerator.new()
	rng.seed = 42

	var lines: Array[String] = []
	for y in BG_ROWS:
		var line = ""
		for x in BG_COLS:
			line += BG_CHARS[rng.randi() % BG_CHARS.length()]

		var fy = y - OFFSET_Y
		if fy >= 0 and fy < face_lines.size():
			var face_line = face_lines[fy]
			var result = ""
			for x in BG_COLS:
				var fx = x - OFFSET_X
				if fx >= 0 and fx < FACE_COLS:
					var fc = face_line[fx]
					if fc != ' ':
						result += fc
						continue
				result += line[x]
			line = result

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

	# Ensure all lines are shown
	$BgLabel.text = "\n".join(_all_lines)

	# Small pause before showing menu
	await get_tree().create_timer(0.15).timeout
	_show_menu()


func _on_start():
	game_state.is_sandbox = false
	game_state.current_level_id = 1
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_sandbox():
	game_state.is_sandbox = true
	game_state.current_level_id = sandbox_data.START_LEVEL
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
