extends LevelLoader
class_name SandboxData

const START_LEVEL := 101

func _ready():
	load_from_file("res://data/sandbox.json")
	print("sandbox_data: loaded ", levels.size(), " levels")
	for lv in levels:
		print("  Level ", lv.id, ": ", lv.name, " (", lv.cols, "x", lv.rows, ")")
