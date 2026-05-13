extends Area2D

const BOX_NORMAL := Rect2(64, 0, 64, 64)
const BOX_ON_TARGET := Rect2(128, 0, 64, 64)

var is_on_target := false:
	set(val):
		is_on_target = val
		_update_visual()

func _update_visual():
	var sprite = get_child(0)
	if sprite is Sprite2D and sprite.region_enabled:
		sprite.region_rect = BOX_ON_TARGET if is_on_target else BOX_NORMAL
