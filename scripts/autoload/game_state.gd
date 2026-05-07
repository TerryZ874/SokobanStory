extends Node

var current_level_id := 1
var progress := {}

func _ready():
	load_progress()

func level_completed(level_id: int, steps: int):
	if not progress.has("completed_levels"):
		progress.completed_levels = {}

	var key = str(level_id)
	var entry = progress.completed_levels.get(key, {})
	if not entry.get("completed", false):
		progress.completed_levels[key] = {"best_steps": steps, "completed": true}
	elif steps < entry.get("best_steps", steps):
		progress.completed_levels[key].best_steps = steps

	if not progress.has("unlocked_levels"):
		progress.unlocked_levels = [1]

	var next_id = level_id + 1
	if next_id <= level_data.get_level_count() and next_id not in progress.unlocked_levels:
		progress.unlocked_levels.append(next_id)

	save_progress()

func save_progress():
	var file = FileAccess.open("user://progress.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.new().stringify(progress))

func load_progress():
	var file = FileAccess.open("user://progress.json", FileAccess.READ)
	if file:
		var json = JSON.new()
		if json.parse(file.get_as_text()) == OK:
			progress = json.data
			return

	progress = {"unlocked_levels": [1], "completed_levels": {}}
