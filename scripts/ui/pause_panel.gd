extends ColorRect

func _ready():
	process_mode = Node.PROCESS_MODE_WHEN_PAUSED

func _input(event):
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		get_parent()._toggle_pause()
		get_viewport().set_input_as_handled()
