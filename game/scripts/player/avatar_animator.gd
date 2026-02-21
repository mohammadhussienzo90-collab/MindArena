extends Node
class_name AvatarAnimator
## Procedural animation for the avatar using tweens (no skeletal animation needed).
## Handles walk cycle, idle bob, XP gain pulse, level-up burst, and portal entry.

var _avatar: AvatarBuilder
var _walk_tween: Tween
var _idle_tween: Tween
var _is_walking := false
var _time := 0.0

const WALK_BOB_AMOUNT := 0.06
const WALK_BOB_SPEED := 0.2
const IDLE_BOB_AMOUNT := 0.03
const IDLE_BOB_SPEED := 0.5
const RING_SPIN_SPEED := 1.0


func setup(avatar: AvatarBuilder) -> void:
	_avatar = avatar
	_start_idle()
	_start_ring_spin()


func _process(delta: float) -> void:
	_time += delta
	# Constant ring spin for energy ring
	if _avatar and _avatar.energy_ring:
		_avatar.energy_ring.rotation.y += RING_SPIN_SPEED * delta


func update_movement(velocity: Vector3) -> void:
	var moving := Vector2(velocity.x, velocity.z).length() > 0.3

	if moving and not _is_walking:
		_is_walking = true
		_stop_idle()
		_start_walk()
	elif not moving and _is_walking:
		_is_walking = false
		_stop_walk()
		_start_idle()


func animate_xp_gain(_amount: int) -> void:
	if not _avatar or not _avatar.energy_ring:
		return
	var tween := _avatar.create_tween()
	tween.tween_property(_avatar.energy_ring, "scale", Vector3(1.6, 1.6, 1.6), 0.15)
	tween.tween_property(_avatar.energy_ring, "scale", Vector3(1.0, 1.0, 1.0), 0.35).set_trans(Tween.TRANS_ELASTIC)


func animate_level_up() -> void:
	if not _avatar:
		return

	# Flash the whole avatar bright
	var tween := _avatar.create_tween()
	tween.set_parallel(true)

	# Energy ring expands massively
	if _avatar.energy_ring:
		tween.tween_property(_avatar.energy_ring, "scale", Vector3(3.0, 3.0, 3.0), 0.3)

	# Body pulse
	if _avatar.body_mesh:
		tween.tween_property(_avatar.body_mesh, "scale", Vector3(1.15, 1.15, 1.15), 0.3)

	tween.chain()

	# Contract back
	if _avatar.energy_ring:
		tween.tween_property(_avatar.energy_ring, "scale", Vector3(1.0, 1.0, 1.0), 0.5).set_trans(Tween.TRANS_ELASTIC)
	if _avatar.body_mesh:
		tween.tween_property(_avatar.body_mesh, "scale", Vector3(1.0, 1.0, 1.0), 0.5).set_trans(Tween.TRANS_ELASTIC)

	# Spawn burst particles
	_spawn_level_up_particles()


func animate_portal_enter() -> void:
	if not _avatar:
		return
	var tween := _avatar.create_tween()
	tween.set_parallel(true)
	tween.tween_property(_avatar, "scale", Vector3(0.01, 0.01, 0.01), 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	tween.tween_property(_avatar, "rotation:y", _avatar.rotation.y + TAU * 2, 0.6)


func _start_walk() -> void:
	if _walk_tween and _walk_tween.is_valid():
		_walk_tween.kill()

	_walk_tween = _avatar.create_tween()
	_walk_tween.set_loops()

	# Body bobs up/down
	if _avatar.body_mesh:
		_walk_tween.tween_property(_avatar.body_mesh, "position:y", 0.55 + WALK_BOB_AMOUNT, WALK_BOB_SPEED).set_trans(Tween.TRANS_SINE)
		_walk_tween.tween_property(_avatar.body_mesh, "position:y", 0.55 - WALK_BOB_AMOUNT, WALK_BOB_SPEED).set_trans(Tween.TRANS_SINE)

	# Shoulder sway
	if _avatar.shoulder_left and _avatar.shoulder_right:
		var sway_tween := _avatar.create_tween()
		sway_tween.set_loops()
		sway_tween.tween_property(_avatar.shoulder_left, "position:z", 0.08, WALK_BOB_SPEED)
		sway_tween.parallel().tween_property(_avatar.shoulder_right, "position:z", -0.08, WALK_BOB_SPEED)
		sway_tween.tween_property(_avatar.shoulder_left, "position:z", -0.08, WALK_BOB_SPEED)
		sway_tween.parallel().tween_property(_avatar.shoulder_right, "position:z", 0.08, WALK_BOB_SPEED)


func _stop_walk() -> void:
	if _walk_tween and _walk_tween.is_valid():
		_walk_tween.kill()
	# Reset positions
	if _avatar and _avatar.body_mesh:
		_avatar.body_mesh.position.y = 0.55
	if _avatar and _avatar.shoulder_left:
		_avatar.shoulder_left.position.z = 0.0
	if _avatar and _avatar.shoulder_right:
		_avatar.shoulder_right.position.z = 0.0


func _start_idle() -> void:
	if _idle_tween and _idle_tween.is_valid():
		_idle_tween.kill()

	if not _avatar or not _avatar.body_mesh:
		return

	_idle_tween = _avatar.create_tween()
	_idle_tween.set_loops()
	_idle_tween.tween_property(_avatar.body_mesh, "position:y", 0.55 + IDLE_BOB_AMOUNT, IDLE_BOB_SPEED).set_trans(Tween.TRANS_SINE)
	_idle_tween.tween_property(_avatar.body_mesh, "position:y", 0.55 - IDLE_BOB_AMOUNT, IDLE_BOB_SPEED).set_trans(Tween.TRANS_SINE)


func _stop_idle() -> void:
	if _idle_tween and _idle_tween.is_valid():
		_idle_tween.kill()


func _spawn_level_up_particles() -> void:
	var particles := GPUParticles3D.new()
	particles.name = "LevelUpBurst"
	particles.position = _avatar.global_position + Vector3(0, 1.0, 0)
	particles.emitting = true
	particles.one_shot = true
	particles.amount = 60
	particles.lifetime = 1.5

	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0.0, 1.0, 0.0)
	mat.spread = 180.0
	mat.initial_velocity_min = 3.0
	mat.initial_velocity_max = 6.0
	mat.gravity = Vector3(0.0, -2.0, 0.0)
	mat.scale_min = 0.05
	mat.scale_max = 0.15
	mat.color = _avatar.accent_color

	particles.process_material = mat

	var draw_mesh := SphereMesh.new()
	draw_mesh.radius = 0.06
	draw_mesh.height = 0.12
	particles.draw_pass_1 = draw_mesh

	_avatar.get_parent().add_child(particles)

	# Auto-cleanup
	var timer := _avatar.get_tree().create_timer(2.0)
	timer.timeout.connect(particles.queue_free)
