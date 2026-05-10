extends Node
class_name LevelLoader

signal data_error(msg)

var levels: Array = []

func load_from_file(path: String) -> bool:
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		var msg = "Cannot open " + path
		emit_signal("data_error", msg)
		push_error(msg)
		return false

	var text = file.get_as_text()
	var json = JSON.new()
	if json.parse(text) != OK:
		var msg = "JSON parse error in " + path
		emit_signal("data_error", msg)
		push_error(msg)
		return false

	var data = json.data
	if not data.has("levels"):
		var msg = "No levels array in " + path
		emit_signal("data_error", msg)
		push_error(msg)
		return false

	levels = data.levels
	for level in levels:
		level.cols = int(level.cols)
		level.rows = int(level.rows)
		if level.has("id"):
			level.id = int(level.id)
		if not _validate_level(level):
			return false

	print("Loaded ", levels.size(), " levels from ", path)
	return true

func _validate_level(level: Dictionary) -> bool:
	if level.grid.size() != level.rows:
		var msg = "Level %d: row count mismatch" % level.id
		emit_signal("data_error", msg)
		push_error(msg)
		return false
	for row in level.grid:
		if row.size() != level.cols:
			var msg = "Level %d: col count mismatch" % level.id
			emit_signal("data_error", msg)
			push_error(msg)
			return false
	return true

func get_level(id: int) -> Dictionary:
	for level in levels:
		if level.id == id:
			return level
	return {}

func get_level_count() -> int:
	return levels.size()

func get_max_dimensions() -> Vector2:
	var mc = 0
	var mr = 0
	for level in levels:
		mc = max(mc, level.cols)
		mr = max(mr, level.rows)
	return Vector2(mc, mr)
