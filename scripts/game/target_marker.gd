extends Node2D

var tile_size: int
var color := Color("#999999")

func _draw():
	var s = tile_size
	var lw = max(1, s * 0.06)
	var cl = s * 0.25      # corner bracket length
	var g = s * 0.08       # gap from edge

	# Four corner brackets
	var corners = [
		[Vector2(g, g + cl), Vector2(g, g), Vector2(g + cl, g)],            # top-left
		[Vector2(s - g - cl, g), Vector2(s - g, g), Vector2(s - g, g + cl)], # top-right
		[Vector2(g, s - g - cl), Vector2(g, s - g), Vector2(g + cl, s - g)], # bottom-left
		[Vector2(s - g - cl, s - g), Vector2(s - g, s - g), Vector2(s - g, s - g - cl)], # bottom-right
	]
	for pts in corners:
		draw_line(pts[0], pts[1], color, lw)
		draw_line(pts[1], pts[2], color, lw)

	# Crosshair in center
	var cx = s * 0.5
	draw_line(Vector2(cx, g * 2.5), Vector2(cx, s - g * 2.5), Color(color.r, color.g, color.b, color.a * 0.5), max(1, lw * 0.4))
	draw_line(Vector2(g * 2.5, cx), Vector2(s - g * 2.5, cx), Color(color.r, color.g, color.b, color.a * 0.5), max(1, lw * 0.4))
