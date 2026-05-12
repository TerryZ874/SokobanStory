extends Node

const SAVE_PATH := "user://save.json"

var current_level := 1
var completed_levels = []
var level_steps := {}
var player_difficulty := {}
var game_completed := false


func save_game():
	var data = {
		"current_level": current_level,
		"completed_levels": completed_levels,
		"level_steps": level_steps,
		"player_difficulty": player_difficulty,
		"game_completed": game_completed,
	}
	var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file:
		file.store_string(JSON.new().stringify(data))


func load_game() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false
	var file = FileAccess.open(SAVE_PATH, FileAccess.READ)
	if not file:
		return false
	var text = file.get_as_text()
	var data = JSON.parse_string(text)
	if typeof(data) != TYPE_DICTIONARY:
		return false
	current_level = data.get("current_level", 1)
	completed_levels = data.get("completed_levels", [])
	level_steps = data.get("level_steps", {})
	player_difficulty = data.get("player_difficulty", {})
	game_completed = data.get("game_completed", false)
	return true


func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)


func delete_save():
	if has_save():
		DirAccess.remove_absolute(SAVE_PATH)
	_reset_state()


func _reset_state():
	current_level = 1
	completed_levels = []
	level_steps = {}
	player_difficulty = {}
	game_completed = false


func set_level_completed(level_id: int):
	if level_id not in completed_levels:
		completed_levels.append(level_id)

	# Check if all main campaign levels are done
	var main_count = level_data.get_level_count()
	game_completed = true
	for lid in range(main_count):
		if (lid + 1) not in completed_levels:
			game_completed = false
			break

	print("save: level ", level_id, " completed, game_completed=", game_completed)
	save_game()


func set_player_difficulty(level_id: int, score: float):
	player_difficulty[str(level_id)] = score
	save_game()


func get_player_difficulty(level_id: int) -> float:
	return player_difficulty.get(str(level_id), 0.0)


func set_level_steps(level_id: int, steps: int):
	var key = str(level_id)
	var prev = level_steps.get(key, 0)
	if prev == 0 or steps < prev:
		level_steps[key] = steps
		save_game()


func get_level_steps(level_id: int) -> int:
	return level_steps.get(str(level_id), 0)
