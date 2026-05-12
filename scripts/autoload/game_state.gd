extends Node

var current_level_id := 1
var pending_story: Array = []
var next_level_after_dialogue: int = 1
var is_password_mode := false

const PASS_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"

func generate_password(level_id: int) -> String:
	var n = level_id * 100000000 + 12345678
	var result = ""
	for i in range(6):
		result = PASS_CHARS[n % 36] + result
		n /= 36
	return result

func level_completed(level_id: int, steps: int):
	save_manager.set_level_completed(level_id)
	save_manager.set_level_steps(level_id, steps)

func validate_password(pwd: String) -> int:
	pwd = pwd.strip_edges().to_lower()
	if pwd.is_empty():
		return -1
	if pwd.length() != 6:
		return -1
	for ch in pwd:
		if PASS_CHARS.find(ch) < 0:
			return -1
	for lid in range(1, level_data.get_level_count() + 1):
		if generate_password(lid) == pwd:
			return lid
	return -1
