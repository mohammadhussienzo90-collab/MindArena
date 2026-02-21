extends Area3D
## Portal to enter a realm. Placed in the world hub.
## Features: torus ring, inner vortex shader, GPU particles, pulsing light, Label3D.

@export var realm_slug: String = ""
@export var realm_display_name: String = ""
@export var portal_color: Color = Color.WHITE
@export var portal_secondary_color: Color = Color(0.1, 0.2, 0.5)

const PULSE_SPEED := 1.2
const PULSE_MIN := 1.5
const PULSE_MAX := 3.0
const PARTICLE_COUNT := 40
const LIGHT_RANGE := 8.0

var _player_nearby := false
var _ring: MeshInstance3D
var _vortex: MeshInstance3D
var _particles: GPUParticles3D
var _light: OmniLight3D
var _label: Label3D
var _interaction_hint: Label3D
var _pulse_tween: Tween


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

	_build_ring()
	_build_vortex()
	_build_particles()
	_build_light()
	_build_label()
	_build_interaction_hint()
	_start_pulse()
	_update_visual_stage()


func _update_visual_stage() -> void:
	var stage: int = PlayerData.get_realm_visual_stage(realm_slug)
	var base_scale := 1.0 + (stage * 0.12)
	scale = Vector3(base_scale, base_scale, base_scale)

	# More particles and brighter light at higher stages
	if _particles:
		_particles.amount = PARTICLE_COUNT + stage * 10
	if _light:
		_light.light_energy = PULSE_MIN + stage * 0.3


func _build_ring() -> void:
	_ring = MeshInstance3D.new()
	_ring.name = "Ring"
	var torus := TorusMesh.new()
	torus.inner_radius = 1.8
	torus.outer_radius = 2.2
	torus.rings = 24
	torus.ring_segments = 16
	_ring.mesh = torus
	_ring.rotation.x = deg_to_rad(90)  # Stand the torus upright
	_ring.position.y = 2.5

	var mat := StandardMaterial3D.new()
	mat.albedo_color = portal_color.darkened(0.3)
	mat.emission_enabled = true
	mat.emission = portal_color
	mat.emission_energy_multiplier = 2.0
	mat.metallic = 0.6
	mat.roughness = 0.2
	_ring.material_override = mat

	add_child(_ring)


func _build_vortex() -> void:
	_vortex = MeshInstance3D.new()
	_vortex.name = "Vortex"
	var quad := QuadMesh.new()
	quad.size = Vector2(3.4, 3.4)
	_vortex.mesh = quad
	_vortex.rotation.x = deg_to_rad(90)  # Face the same direction as the ring
	_vortex.position.y = 2.5

	# Apply vortex shader
	var shader := load("res://assets/shaders/portal_vortex.gdshader") as Shader
	if shader:
		var mat := ShaderMaterial.new()
		mat.shader = shader
		mat.set_shader_parameter("portal_color", Vector3(portal_color.r, portal_color.g, portal_color.b))
		mat.set_shader_parameter("secondary_color", Vector3(portal_secondary_color.r, portal_secondary_color.g, portal_secondary_color.b))
		mat.set_shader_parameter("time_scale", 1.5)
		mat.set_shader_parameter("swirl_arms", 4.0)
		mat.set_shader_parameter("intensity", 2.5)
		mat.set_shader_parameter("pulse_speed", PULSE_SPEED)
		_vortex.material_override = mat
	else:
		# Fallback if shader not found
		var mat := StandardMaterial3D.new()
		mat.albedo_color = portal_color
		mat.emission_enabled = true
		mat.emission = portal_color
		mat.emission_energy_multiplier = 2.0
		_vortex.material_override = mat

	add_child(_vortex)


func _build_particles() -> void:
	_particles = GPUParticles3D.new()
	_particles.name = "Particles"
	_particles.position.y = 2.5

	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0.0, 1.0, 0.0)
	mat.spread = 40.0
	mat.initial_velocity_min = 0.5
	mat.initial_velocity_max = 2.0
	mat.gravity = Vector3(0.0, 0.3, 0.0)
	mat.damping_min = 0.3
	mat.damping_max = 0.8

	# Emit from ring shape
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_RING
	mat.emission_ring_radius = 2.0
	mat.emission_ring_inner_radius = 1.5
	mat.emission_ring_height = 0.3
	mat.emission_ring_axis = Vector3(0.0, 1.0, 0.0)

	# Scale
	mat.scale_min = 0.04
	mat.scale_max = 0.12

	# Color with fade
	mat.color = Color(portal_color, 0.7)

	_particles.process_material = mat
	_particles.amount = PARTICLE_COUNT
	_particles.lifetime = 2.5
	_particles.randomness = 0.4
	_particles.visibility_aabb = AABB(Vector3(-5, -3, -5), Vector3(10, 8, 10))

	var draw_mesh := SphereMesh.new()
	draw_mesh.radius = 0.06
	draw_mesh.height = 0.12
	_particles.draw_pass_1 = draw_mesh

	add_child(_particles)


func _build_light() -> void:
	_light = OmniLight3D.new()
	_light.name = "PortalLight"
	_light.position.y = 2.5
	_light.light_color = portal_color
	_light.light_energy = PULSE_MIN
	_light.omni_range = LIGHT_RANGE
	_light.omni_attenuation = 1.5
	_light.shadow_enabled = false
	add_child(_light)


func _build_label() -> void:
	_label = Label3D.new()
	_label.name = "Label3D"
	_label.text = realm_display_name
	_label.font_size = 48
	_label.outline_size = 8
	_label.modulate = Color(portal_color, 0.9)
	_label.position.y = 5.5
	_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(_label)


func _build_interaction_hint() -> void:
	_interaction_hint = Label3D.new()
	_interaction_hint.name = "InteractionHint"
	_interaction_hint.text = "Press E to enter"
	_interaction_hint.font_size = 28
	_interaction_hint.outline_size = 6
	_interaction_hint.modulate = Color(1.0, 1.0, 1.0, 0.0)  # Start invisible
	_interaction_hint.position.y = 4.8
	_interaction_hint.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(_interaction_hint)


func _start_pulse() -> void:
	_animate_pulse()


func _animate_pulse() -> void:
	if not is_inside_tree():
		return
	_pulse_tween = create_tween()
	_pulse_tween.set_loops()
	_pulse_tween.tween_property(_light, "light_energy", PULSE_MAX, 0.8).set_trans(Tween.TRANS_SINE)
	_pulse_tween.tween_property(_light, "light_energy", PULSE_MIN, 0.8).set_trans(Tween.TRANS_SINE)


func _unhandled_input(event: InputEvent) -> void:
	if _player_nearby and event.is_action_pressed("interact"):
		_enter_realm()


func _enter_realm() -> void:
	GameManager.enter_realm(realm_slug)
	print("[Portal] Entering realm: %s" % realm_slug)


func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("player"):
		_player_nearby = true
		_show_interaction_hint(true)
		if body.has_method("set_nearby_portal"):
			body.set_nearby_portal(self)


func _on_body_exited(body: Node3D) -> void:
	if body.is_in_group("player"):
		_player_nearby = false
		_show_interaction_hint(false)
		if body.has_method("clear_nearby_portal"):
			body.clear_nearby_portal(self)


func _show_interaction_hint(show: bool) -> void:
	if not _interaction_hint:
		return
	var tween := create_tween()
	if show:
		tween.tween_property(_interaction_hint, "modulate:a", 0.9, 0.3)
	else:
		tween.tween_property(_interaction_hint, "modulate:a", 0.0, 0.3)
