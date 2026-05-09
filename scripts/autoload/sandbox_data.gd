extends Node
class_name SandboxData

signal data_error(msg)

var levels: Array = []

func _ready():
	load_sandbox_levels()

func load_sandbox_levels():
	var file = FileAccess.open("res://data/sandbox.json", FileAccess.READ)
	if file == null:
		emit_signal("data_error", "sandbox: Cannot open sandbox.json")
		push_error("sandbox_data: Cannot open sandbox.json")
		return

	var text = file.get_as_text()
	var json = JSON.new()
	if json.parse(text) != OK:
		emit_signal("data_error", "sandbox: JSON parse error")
		push_error("sandbox_data: JSON parse error")
		return

	var data = json.data
	if not data.has("levels"):
		emit_signal("data_error", "sandbox: No levels array in data")
		push_error("sandbox_data: No levels array")
		return

	levels = data.levels
	for level in levels:
		level.cols = int(level.cols)
		level.rows = int(level.rows)
		level.id = int(level.id)
		_validate_level(level)

	print("sandbox_data: loaded ", levels.size(), " levels")
	for lv in levels:
		print("  Level ", lv.id, ": ", lv.name, " (", lv.cols, "x", lv.rows, ")")

func _validate_level(level: Dictionary) -> bool:
	if level.grid.size() != level.rows:
		emit_signal("data_error", "sandbox Level %d: row count mismatch" % level.id)
		push_error("sandbox_data: Level %d: row count mismatch" % level.id)
		return false
	for row in level.grid:
		if row.size() != level.cols:
			emit_signal("data_error", "sandbox Level %d: col count mismatch" % level.id)
			push_error("sandbox_data: Level %d: col count mismatch" % level.id)
			return false
	return true

func get_level(id: int) -> Dictionary:
	for level in levels:
		if level.id == id:
			return level
	push_error("sandbox_data: Level %d not found" % id)
	return {}

func get_level_count() -> int:
	return levels.size()
