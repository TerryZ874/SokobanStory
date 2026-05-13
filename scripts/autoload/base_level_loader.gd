extends Node
class_name LevelLoader

signal data_error(msg)

var levels: Array = []           # metadata only (no grid)
var _full_levels: Dictionary = {} # id → full level dict (with grid), lazy-loaded
var _levels_by_id: Dictionary = {} # id → metadata dict, for O(1) lookup
var _full_file_path: String = ""
var _full_loaded := false

func load_from_file(path: String) -> bool:
	return _do_load(path, false)

func load_metadata_from_file(meta_path: String, full_path: String = "") -> bool:
	var ok = _do_load(meta_path, true)
	if ok and full_path != "":
		_full_file_path = full_path
	return ok

func _do_load(path: String, is_meta: bool) -> bool:
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
		_levels_by_id[level.id] = level
		if not is_meta:
			if not _validate_level(level):
				return false

	print("Loaded ", levels.size(), " levels from ", path)
	return true

func _load_full_levels():
	if _full_loaded or _full_file_path == "":
		return
	var file = FileAccess.open(_full_file_path, FileAccess.READ)
	if file == null:
		push_error("Cannot open full levels: " + _full_file_path)
		return
	var json = JSON.new()
	if json.parse(file.get_as_text()) != OK:
		push_error("JSON parse error in " + _full_file_path)
		return
	var data = json.data
	if not data.has("levels"):
		return
	for lv in data.levels:
		lv.cols = int(lv.cols)
		lv.rows = int(lv.rows)
		if lv.has("id"):
			lv.id = int(lv.id)
		_full_levels[lv.id] = lv
	_full_loaded = true
	print("Full levels loaded (with grids): ", _full_levels.size())

func _validate_level(level: Dictionary) -> bool:
	if not level.has("grid"):
		# metadata-only mode, no grid validation
		return true
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
	return _levels_by_id.get(id, {})

func get_full_level(id: int) -> Dictionary:
	# Returns level with grid data; lazy-loads full file if needed
	if _full_levels.has(id):
		return _full_levels[id]
	_load_full_levels()
	return _full_levels.get(id, {})

func get_level_count() -> int:
	return levels.size()

func get_max_dimensions() -> Vector2:
	var mc = 0
	var mr = 0
	for level in levels:
		mc = max(mc, level.cols)
		mr = max(mr, level.rows)
	return Vector2(mc, mr)
