extends Node3D
class_name NoorVisual
## Visual representation of the Noor AI companion.
## A glowing orb that follows the player with gentle bobbing and sparkle particles.
## Changes color and intensity based on companion mood/state.

const FOLLOW_OFFSET := Vector3(1.5, 1.8, -0.8)
const BOB_SPEED := 2.5
const BOB_AMOUNT := 0.12
const FOLLOW_SPEED := 3.5
const ORBIT_SPEED := 0.3
const ORBIT_RADIUS := 0.3

const NOOR_COLOR := Color(0.2, 0.85, 0.9)       # Teal — Noor's signature color
const NOOR_INNER := Color(0.8, 0.95, 1.0)        # Bright white-teal inner core
const PARTICLE_COLOR := Color(0.3, 0.9, 1.0, 0.5)

var _target: Node3D
var _time := 0.0
var _orb: MeshInstance3D
var _inner_core: MeshInstance3D
var _light: OmniLight3D
var _particles: GPUParticles3D
var _mood: String = "neutral"  # neutral, happy, thinking, alert


func _ready() -> void:
	_build_orb()
	_build_inner_core()
	_build_light()
	_build_sparkle_trail()


func set_target(target: Node3D) -> void:
	_target = target


func set_mood(mood: String) -> void:
	_mood = mood
	_update_mood_visual()


func _process(delta: float) -> void:
	_time += delta

	if not _target:
		return

	# Calculate follow position with orbit
	var orbit_offset := Vector3(
		cos(_time * ORBIT_SPEED) * ORBIT_RADIUS,
		0.0,
		sin(_time * ORBIT_SPEED) * ORBIT_RADIUS
	)
	var target_pos: Vector3 = _target.global_position + FOLLOW_OFFSET + orbit_offset

	# Gentle bobbing
	target_pos.y += sin(_time * BOB_SPEED) * BOB_AMOUNT

	# Smooth follow
	global_position = global_position.lerp(target_pos, FOLLOW_SPEED * delta)

	# Inner core pulsing
	if _inner_core:
		var pulse := 0.8 + sin(_time * 3.0) * 0.2
		_inner_core.scale = Vector3.ONE * pulse * 0.5

	# Light pulsing
	if _light:
		_light.light_energy = 1.5 + sin(_time * 2.5) * 0.5


func _build_orb() -> void:
	_orb = MeshInstance3D.new()
	_orb.name = "NoorOrb"
	var sphere := SphereMesh.new()
	sphere.radius = 0.18
	sphere.height = 0.36
	sphere.radial_segments = 16
	sphere.rings = 12
	_orb.mesh = sphere

	var mat := StandardMaterial3D.new()
	mat.albedo_color = NOOR_COLOR
	mat.emission_enabled = true
	mat.emission = NOOR_COLOR
	mat.emission_energy_multiplier = 3.0
	mat.metallic = 0.4
	mat.roughness = 0.1
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color.a = 0.8
	_orb.material_override = mat

	add_child(_orb)


func _build_inner_core() -> void:
	_inner_core = MeshInstance3D.new()
	_inner_core.name = "InnerCore"
	var sphere := SphereMesh.new()
	sphere.radius = 0.1
	sphere.height = 0.2
	_inner_core.mesh = sphere
	_inner_core.scale = Vector3(0.5, 0.5, 0.5)

	var mat := StandardMaterial3D.new()
	mat.albedo_color = NOOR_INNER
	mat.emission_enabled = true
	mat.emission = NOOR_INNER
	mat.emission_energy_multiplier = 5.0
	_inner_core.material_override = mat

	add_child(_inner_core)


func _build_light() -> void:
	_light = OmniLight3D.new()
	_light.name = "NoorLight"
	_light.light_color = NOOR_COLOR
	_light.light_energy = 2.0
	_light.omni_range = 5.0
	_light.omni_attenuation = 2.0
	_light.shadow_enabled = false
	add_child(_light)


func _build_sparkle_trail() -> void:
	_particles = GPUParticles3D.new()
	_particles.name = "SparkleTrail"

	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0.0, 0.5, 0.0)
	mat.spread = 60.0
	mat.initial_velocity_min = 0.2
	mat.initial_velocity_max = 0.8
	mat.gravity = Vector3(0.0, -0.5, 0.0)
	mat.damping_min = 1.0
	mat.damping_max = 2.0
	mat.scale_min = 0.02
	mat.scale_max = 0.06
	mat.color = PARTICLE_COLOR

	_particles.process_material = mat
	_particles.amount = 15
	_particles.lifetime = 1.5
	_particles.randomness = 0.5
	_particles.visibility_aabb = AABB(Vector3(-2, -2, -2), Vector3(4, 4, 4))

	var draw_mesh := SphereMesh.new()
	draw_mesh.radius = 0.03
	draw_mesh.height = 0.06
	_particles.draw_pass_1 = draw_mesh

	add_child(_particles)


func _update_mood_visual() -> void:
	var target_color: Color
	var target_energy: float
	var target_particle_amount: int

	match _mood:
		"happy":
			target_color = Color(0.3, 1.0, 0.5)  # Green-teal
			target_energy = 4.0
			target_particle_amount = 25
		"thinking":
			target_color = Color(0.5, 0.4, 1.0)  # Purple
			target_energy = 2.5
			target_particle_amount = 20
		"alert":
			target_color = Color(1.0, 0.7, 0.2)  # Golden
			target_energy = 5.0
			target_particle_amount = 30
		_:  # neutral
			target_color = NOOR_COLOR
			target_energy = 3.0
			target_particle_amount = 15

	_particles.amount = target_particle_amount

	if _orb and _orb.material_override:
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(_orb.material_override, "emission", target_color, 0.5)
		tween.tween_property(_orb.material_override, "albedo_color", Color(target_color, 0.8), 0.5)
		tween.tween_property(_orb.material_override, "emission_energy_multiplier", target_energy, 0.5)
		if _light:
			tween.tween_property(_light, "light_color", target_color, 0.5)
