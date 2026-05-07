extends Node

var data: Dictionary = {}

func _ready():
	load_story()

func load_story():
	var file = FileAccess.open("res://data/story.json", FileAccess.READ)
	if file == null:
		push_error("story_data: Cannot open story.json")
		return

	var json = JSON.new()
	if json.parse(file.get_as_text()) != OK:
		push_error("story_data: JSON parse error")
		return

	data = json.data

func get_story(level_id: int) -> Array:
	var key = str(level_id)
	if data.has("stories") and data.stories.has(key):
		return data.stories[key]
	return []

func get_character(char_id: String) -> Dictionary:
	if data.has("characters") and data.characters.has(char_id):
		return data.characters[char_id]
	return {}
