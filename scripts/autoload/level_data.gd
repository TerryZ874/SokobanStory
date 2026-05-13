extends LevelLoader

func _ready():
	# Load metadata only at startup (fast, no grid data)
	load_metadata_from_file("res://data/levels_meta.json", "res://data/levels.json")
	print("Level data ready: ", get_level_count(), " levels (metadata only, grids lazy-loaded)")
