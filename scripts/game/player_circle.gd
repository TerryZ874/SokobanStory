extends Node2D

var tile_size: int
var color := Color("#4ecdc4"):
	set(value):
		color = value
		queue_redraw()

func _draw():
	var r = tile_size * 0.25
	draw_circle(Vector2.ZERO, r, color)
