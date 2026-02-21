extends Node3D
class_name XPPopup
## Floating "+X XP" text that rises and fades out.
## Spawned at a 3D position, uses billboard mode to always face camera.

const RISE_DISTANCE := 2.5
const DURATION := 1.8
const XP_COLOR := Color(1.0, 0.85, 0.15, 1.0)
const BONUS_COLOR := Color(0.3, 1.0, 0.5, 1.0)
const LEVEL_COLOR := Color(1.0, 0.5, 0.9, 1.0)


static func spawn(parent: Node3D, world_position: Vector3, amount: int, is_bonus: bool = false) -> void:
	var popup := XPPopup.new()
	popup.position = world_position + Vector3(0.0, 1.5, 0.0)
	parent.add_child(popup)
	popup._animate(amount, is_bonus)


static func spawn_level_up(parent: Node3D, world_position: Vector3, new_level: int) -> void:
	var popup := XPPopup.new()
	popup.position = world_position + Vector3(0.0, 2.0, 0.0)
	parent.add_child(popup)
	popup._animate_level_up(new_level)


func _animate(amount: int, is_bonus: bool) -> void:
	var label := Label3D.new()
	label.text = "+%d XP" % amount
	label.font_size = 36 if not is_bonus else 42
	label.outline_size = 8
	label.modulate = BONUS_COLOR if is_bonus else XP_COLOR
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.render_priority = 10
	add_child(label)

	# Slight random horizontal offset
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var x_offset := rng.randf_range(-0.3, 0.3)

	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(self, "position:y", position.y + RISE_DISTANCE, DURATION).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position:x", position.x + x_offset, DURATION)
	tween.tween_property(label, "modulate:a", 0.0, DURATION).set_delay(DURATION * 0.3)

	# Scale up then shrink
	tween.tween_property(label, "font_size", label.font_size + 8, 0.2)
	var shrink_tween := create_tween()
	shrink_tween.tween_interval(0.2)
	shrink_tween.tween_property(label, "font_size", label.font_size, 0.3)

	await tween.finished
	queue_free()


func _animate_level_up(new_level: int) -> void:
	var label := Label3D.new()
	label.text = "LEVEL %d!" % new_level
	label.font_size = 52
	label.outline_size = 12
	label.modulate = LEVEL_COLOR
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.render_priority = 10
	add_child(label)

	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(self, "position:y", position.y + RISE_DISTANCE * 1.5, 2.5).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(label, "modulate:a", 0.0, 2.5).set_delay(1.0)

	# Pulse scale
	var scale_tween := create_tween()
	scale_tween.set_loops(3)
	scale_tween.tween_property(self, "scale", Vector3(1.2, 1.2, 1.2), 0.15)
	scale_tween.tween_property(self, "scale", Vector3(1.0, 1.0, 1.0), 0.15)

	await tween.finished
	queue_free()
