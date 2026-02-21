extends Node3D
class_name IntroCinematic
## Scripted camera fly-through for first-time players.
## Plays at first login (onboarding_done == false) before giving player control.
## Uses tween-based camera animation with dialogue overlays.

signal cinematic_started()
signal cinematic_ended()

var _camera: Camera3D
var _dialogue_manager: DialogueManager
var _dialogue_ui: DialogueUI
var _player: CharacterBody3D
var _noor: NoorVisual
var _is_playing := false


func play(player: CharacterBody3D, camera: Camera3D) -> void:
	"""Start the intro cinematic. Disables player control during playback."""
	if _is_playing:
		return

	_is_playing = true
	_player = player
	_camera = camera
	cinematic_started.emit()

	# Disable player movement
	_player.set_physics_process(false)
	_player.set_process_unhandled_input(false)

	# Setup dialogue system
	_dialogue_manager = DialogueManager.new()
	_dialogue_manager.name = "CinematicDialogue"
	add_child(_dialogue_manager)

	_dialogue_ui = DialogueUI.new()
	_dialogue_ui.name = "CinematicDialogueUI"
	add_child(_dialogue_ui)

	# Connect dialogue_ui to our local dialogue_manager manually
	_dialogue_manager.dialogue_started.connect(_dialogue_ui._on_dialogue_started)
	_dialogue_manager.dialogue_line.connect(_dialogue_ui._on_dialogue_line)
	_dialogue_manager.dialogue_ended.connect(_dialogue_ui._on_dialogue_ended)
	_dialogue_manager.dialogue_ended.connect(_on_intro_dialogue_ended)

	await _run_cinematic()


func _run_cinematic() -> void:
	# Store original camera transform
	var original_parent := _camera.get_parent()
	var original_transform := _camera.transform

	# Detach camera from player for cinematic movement
	var camera_holder := Node3D.new()
	camera_holder.name = "CinematicCameraHolder"
	get_parent().add_child(camera_holder)

	# Reparent camera
	_camera.get_parent().remove_child(_camera)
	camera_holder.add_child(_camera)

	# === PHASE 1: High above, looking down at dark world ===
	camera_holder.global_position = Vector3(0, 40, 40)
	_camera.global_transform = Transform3D.IDENTITY
	_camera.look_at(Vector3.ZERO, Vector3.UP)

	await get_tree().create_timer(1.0).timeout

	# === PHASE 2: Slowly descend toward the hub ===
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(camera_holder, "global_position", Vector3(10, 20, 25), 4.0) \
		.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)

	# Start dialogue after a moment
	await get_tree().create_timer(1.5).timeout
	_dialogue_manager.start_dialogue("intro")

	# Wait for the fly tween to finish
	await tween.finished

	# === PHASE 3: Circle around to see portals ===
	var tween2 := create_tween()
	tween2.set_parallel(true)
	tween2.tween_property(camera_holder, "global_position", Vector3(-5, 8, 15), 5.0) \
		.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)

	await tween2.finished

	# Spawn Noor during the cinematic
	_spawn_cinematic_noor()

	# === PHASE 4: Move behind player position ===
	var player_pos: Vector3 = _player.global_position
	var behind_player := player_pos + Vector3(0, 3, 6)

	var tween3 := create_tween()
	tween3.tween_property(camera_holder, "global_position", behind_player, 3.0) \
		.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)

	await tween3.finished

	# Wait for dialogue to end if still active
	if _dialogue_manager.is_active():
		await _dialogue_manager.dialogue_ended

	# === CLEANUP: Return camera to player ===
	camera_holder.remove_child(_camera)
	original_parent.add_child(_camera)
	_camera.transform = original_transform
	camera_holder.queue_free()

	# Cleanup cinematic nodes
	if _noor:
		_noor.queue_free()
	_dialogue_ui.queue_free()
	_dialogue_manager.queue_free()

	# Re-enable player
	_player.set_physics_process(true)
	_player.set_process_unhandled_input(true)
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

	_is_playing = false
	cinematic_ended.emit()


func _spawn_cinematic_noor() -> void:
	_noor = NoorVisual.new()
	_noor.name = "CinematicNoor"
	_noor.global_position = Vector3(2, 3, 2)
	get_parent().add_child(_noor)

	# Animate Noor appearing with scale tween
	_noor.scale = Vector3.ZERO
	var tween := create_tween()
	tween.tween_property(_noor, "scale", Vector3.ONE, 0.8) \
		.set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


func _on_intro_dialogue_ended(_id: String) -> void:
	# Dialogue is done — cinematic will clean up in _run_cinematic
	pass
