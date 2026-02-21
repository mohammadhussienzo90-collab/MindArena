extends Node3D
class_name AvatarBuilder
## Builds a stylized procedural avatar from primitive meshes.
## No external 3D models required — character is constructed from capsules, spheres, and a torus ring.
## Colors are configurable from player profile (avatar_colors JSON field).

@export var body_color: Color = Color(0.25, 0.45, 0.85)
@export var accent_color: Color = Color(0.85, 0.65, 0.15)
@export var skin_color: Color = Color(0.75, 0.6, 0.5)
@export var glow_intensity: float = 0.6

# Node references for animation
var body_mesh: MeshInstance3D
var head_mesh: MeshInstance3D
var eye_left: MeshInstance3D
var eye_right: MeshInstance3D
var energy_ring: MeshInstance3D
var shoulder_left: MeshInstance3D
var shoulder_right: MeshInstance3D

var _built := false


func _ready() -> void:
	if not _built:
		build()


func build() -> void:
	# Clear existing children if rebuilding
	for child in get_children():
		child.queue_free()

	_build_body()
	_build_head()
	_build_eyes()
	_build_energy_ring()
	_build_shoulders()
	_build_feet()
	_built = true


func apply_colors(colors: Dictionary) -> void:
	if colors.has("body"):
		body_color = Color.from_string(colors["body"], body_color)
	if colors.has("accent"):
		accent_color = Color.from_string(colors["accent"], accent_color)
	if colors.has("skin"):
		skin_color = Color.from_string(colors["skin"], skin_color)
	if colors.has("glow"):
		glow_intensity = float(colors["glow"])
	if _built:
		build()


func _build_body() -> void:
	body_mesh = MeshInstance3D.new()
	body_mesh.name = "Body"
	var capsule := CapsuleMesh.new()
	capsule.radius = 0.32
	capsule.height = 1.1
	body_mesh.mesh = capsule
	body_mesh.position.y = 0.55
	body_mesh.material_override = _make_material(body_color, glow_intensity * 0.3)
	add_child(body_mesh)


func _build_head() -> void:
	head_mesh = MeshInstance3D.new()
	head_mesh.name = "Head"
	var sphere := SphereMesh.new()
	sphere.radius = 0.24
	sphere.height = 0.48
	head_mesh.mesh = sphere
	head_mesh.position.y = 1.35
	head_mesh.material_override = _make_material(skin_color.lerp(body_color, 0.3), glow_intensity * 0.2)
	add_child(head_mesh)


func _build_eyes() -> void:
	# Eye whites
	eye_left = _make_eye(-0.09, 1.38, 0.2)
	eye_left.name = "EyeLeft"
	add_child(eye_left)

	eye_right = _make_eye(0.09, 1.38, 0.2)
	eye_right.name = "EyeRight"
	add_child(eye_right)

	# Pupils
	var pupil_left := _make_pupil(-0.09, 1.38, 0.23)
	pupil_left.name = "PupilLeft"
	add_child(pupil_left)

	var pupil_right := _make_pupil(0.09, 1.38, 0.23)
	pupil_right.name = "PupilRight"
	add_child(pupil_right)


func _make_eye(x: float, y: float, z: float) -> MeshInstance3D:
	var eye := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.05
	sphere.height = 0.1
	eye.mesh = sphere
	eye.position = Vector3(x, y, z)
	eye.material_override = _make_material(Color.WHITE, 1.2)
	return eye


func _make_pupil(x: float, y: float, z: float) -> MeshInstance3D:
	var pupil := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.025
	sphere.height = 0.05
	pupil.mesh = sphere
	pupil.position = Vector3(x, y, z)
	pupil.material_override = _make_material(Color(0.05, 0.05, 0.1), 0.0)
	return pupil


func _build_energy_ring() -> void:
	energy_ring = MeshInstance3D.new()
	energy_ring.name = "EnergyRing"
	var torus := TorusMesh.new()
	torus.inner_radius = 0.32
	torus.outer_radius = 0.38
	torus.rings = 16
	torus.ring_segments = 12
	energy_ring.mesh = torus
	energy_ring.position.y = 0.55
	energy_ring.material_override = _make_material(accent_color, glow_intensity * 2.5)
	add_child(energy_ring)


func _build_shoulders() -> void:
	# Simple sphere shoulders for shape definition
	shoulder_left = MeshInstance3D.new()
	shoulder_left.name = "ShoulderLeft"
	var sphere_l := SphereMesh.new()
	sphere_l.radius = 0.12
	sphere_l.height = 0.24
	shoulder_left.mesh = sphere_l
	shoulder_left.position = Vector3(-0.38, 0.9, 0.0)
	shoulder_left.material_override = _make_material(body_color.lightened(0.1), glow_intensity * 0.2)
	add_child(shoulder_left)

	shoulder_right = MeshInstance3D.new()
	shoulder_right.name = "ShoulderRight"
	var sphere_r := SphereMesh.new()
	sphere_r.radius = 0.12
	sphere_r.height = 0.24
	shoulder_right.mesh = sphere_r
	shoulder_right.position = Vector3(0.38, 0.9, 0.0)
	shoulder_right.material_override = _make_material(body_color.lightened(0.1), glow_intensity * 0.2)
	add_child(shoulder_right)


func _build_feet() -> void:
	for i in [-1, 1]:
		var foot := MeshInstance3D.new()
		foot.name = "Foot_%s" % ("L" if i == -1 else "R")
		var box := BoxMesh.new()
		box.size = Vector3(0.15, 0.08, 0.22)
		foot.mesh = box
		foot.position = Vector3(i * 0.15, 0.04, 0.02)
		foot.material_override = _make_material(body_color.darkened(0.3), 0.0)
		add_child(foot)


func _make_material(color: Color, emission_strength: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	if emission_strength > 0.01:
		mat.emission_enabled = true
		mat.emission = color
		mat.emission_energy_multiplier = emission_strength
	mat.metallic = 0.15
	mat.roughness = 0.55
	return mat
