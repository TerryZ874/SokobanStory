extends Node

signal data_error(msg)

var levels: Array = []

func _ready():
	load_levels()

func load_levels():
	var file = FileAccess.open("res://data/levels.json", FileAccess.READ)
	if file == null:
		emit_signal("data_error", "Cannot open levels.json")
		return

	var text = file.get_as_text()
	var json = JSON.new()
	if json.parse(text) != OK:
		emit_signal("data_error", "JSON parse error")
		return

	var data = json.data
	if not data.has("levels"):
		emit_signal("data_error", "No levels array in data")
		return

	levels = data.levels
	for level in levels:
		level.cols = int(level.cols)
		level.rows = int(level.rows)
		_validate_level(level)

func _validate_level(level: Dictionary) -> bool:
	if level.grid.size() != level.rows:
		emit_signal("data_error", "Level %d: row count mismatch" % level.id)
		return false
	for row in level.grid:
		if row.size() != level.cols:
			emit_signal("data_error", "Level %d: col count mismatch" % level.id)
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
