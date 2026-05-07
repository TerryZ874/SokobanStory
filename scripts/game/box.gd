extends Area2D

var is_on_target := false:
	set(val):
		is_on_target = val
		_update_visual()

func _update_visual():
	var sprite = get_child(0)
	if sprite is ColorRect:
		sprite.color = Color("#4CAF50") if is_on_target else Color("#d4a574")
