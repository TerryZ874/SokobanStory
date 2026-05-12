extends Node2D

var tile_size: int
var color := Color("#cccccc")

func _draw():
	var r = tile_size * 0.0375
	draw_circle(Vector2.ZERO, r, color)
