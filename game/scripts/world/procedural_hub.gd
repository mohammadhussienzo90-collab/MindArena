extends Node3D
class_name ProceduralHub
## Generates a procedural floating island terrain for the world hub.
## Uses FastNoiseLite for terrain displacement and a custom shader for rendering.
## Replaces the flat BoxMesh ground with a visually stunning floating island.

const TERRAIN_SIZE := 80.0
const TERRAIN_SUBDIVISIONS := 64
const NOISE_FREQUENCY := 0.018
const TERRAIN_HEIGHT := 4.0
const CLIFF_DROP := 25.0
const ISLAND_RADIUS := 38.0

# Decorative elements
const ROCK_COUNT := 20
const CRYSTAL_COUNT := 8
const GLOW_PLANT_COUNT := 15

var _noise: FastNoiseLite
var _terrain_mesh_instance: MeshInstance3D
var _collision_body: StaticBody3D


func _ready() -> void:
	_noise = FastNoiseLite.new()
	_noise.seed = 42
	_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	_noise.frequency = NOISE_FREQUENCY
	_noise.fractal_type = FastNoiseLite.FRACTAL_FBM
	_noise.fractal_octaves = 4
	_noise.fractal_lacunarity = 2.0
	_noise.fractal_gain = 0.5

	_build_terrain()
	_build_decorations()
	_build_edge_particles()


func _build_terrain() -> void:
	# Create base plane mesh
	var plane_mesh := PlaneMesh.new()
	plane_mesh.size = Vector2(TERRAIN_SIZE, TERRAIN_SIZE)
	plane_mesh.subdivide_depth = TERRAIN_SUBDIVISIONS
	plane_mesh.subdivide_width = TERRAIN_SUBDIVISIONS

	# Convert to ArrayMesh for vertex manipulation
	var surface_tool := SurfaceTool.new()
	surface_tool.create_from(plane_mesh, 0)
	var array_mesh := surface_tool.commit()

	# Displace vertices using noise
	var mesh_data := MeshDataTool.new()
	mesh_data.create_from_surface(array_mesh, 0)

	for i in range(mesh_data.get_vertex_count()):
		var vertex := mesh_data.get_vertex(i)

		# Distance from center normalized to island radius
		var dist_from_center := Vector2(vertex.x, vertex.z).length() / ISLAND_RADIUS

		# Island shape: raised center, falls off at edges
		var island_mask := clamp(1.0 - dist_from_center * dist_from_center, 0.0, 1.0)
		island_mask = island_mask * island_mask  # Sharper falloff

		# Noise displacement
		var height := _noise.get_noise_2d(vertex.x, vertex.z) * TERRAIN_HEIGHT * island_mask

		# Add gentle rolling hills in the center
		var hills := sin(vertex.x * 0.1) * cos(vertex.z * 0.12) * 1.5 * island_mask
		height += hills

		# Cliff edges — dramatic drop past the island boundary
		if dist_from_center > 0.85:
			var cliff_factor := (dist_from_center - 0.85) / 0.15
			height -= cliff_factor * cliff_factor * CLIFF_DROP
		elif dist_from_center > 0.75:
			# Slight lip before the cliff
			var lip := (dist_from_center - 0.75) / 0.10
			height += sin(lip * PI) * 0.5

		vertex.y = height
		mesh_data.set_vertex(i, vertex)

	# Rebuild mesh with recalculated normals
	array_mesh.clear_surfaces()
	mesh_data.commit_to_surface(array_mesh)

	# Recalculate normals for proper lighting
	surface_tool.clear()
	surface_tool.create_from(array_mesh, 0)
	surface_tool.generate_normals()
	surface_tool.generate_tangents()
	array_mesh = surface_tool.commit()

	# Create mesh instance with terrain shader
	_terrain_mesh_instance = MeshInstance3D.new()
	_terrain_mesh_instance.mesh = array_mesh
	_terrain_mesh_instance.material_override = _create_terrain_material()
	_terrain_mesh_instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(_terrain_mesh_instance)

	# Create collision for player to walk on
	_collision_body = StaticBody3D.new()
	_collision_body.collision_layer = 1  # Environment layer
	var collision_shape := CollisionShape3D.new()
	collision_shape.shape = array_mesh.create_trimesh_shape()
	_collision_body.add_child(collision_shape)
	add_child(_collision_body)


func _create_terrain_material() -> ShaderMaterial:
	var shader := load("res://assets/shaders/hub_terrain.gdshader") as Shader
	var mat := ShaderMaterial.new()
	mat.shader = shader
	mat.set_shader_parameter("color_top", Color(0.18, 0.42, 0.22))
	mat.set_shader_parameter("color_mid", Color(0.35, 0.25, 0.15))
	mat.set_shader_parameter("color_bottom", Color(0.12, 0.10, 0.08))
	mat.set_shader_parameter("color_cliff", Color(0.08, 0.06, 0.12))
	mat.set_shader_parameter("height_range", TERRAIN_HEIGHT)
	mat.set_shader_parameter("glow_intensity", 0.15)
	mat.set_shader_parameter("glow_color", Color(0.2, 0.5, 1.0))
	return mat


func _build_decorations() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 123

	# Scatter rocks across the island
	for i in range(ROCK_COUNT):
		var pos := _random_island_position(rng, 0.7)
		var height := _get_terrain_height(pos.x, pos.z)
		if height < -2.0:
			continue
		pos.y = height
		var rock := _create_rock(rng)
		rock.position = pos
		rock.rotation.y = rng.randf() * TAU
		add_child(rock)

	# Glowing crystals near the center
	for i in range(CRYSTAL_COUNT):
		var pos := _random_island_position(rng, 0.4)
		var height := _get_terrain_height(pos.x, pos.z)
		pos.y = height
		var crystal := _create_crystal(rng)
		crystal.position = pos
		crystal.rotation.y = rng.randf() * TAU
		add_child(crystal)

	# Glowing plants scattered around
	for i in range(GLOW_PLANT_COUNT):
		var pos := _random_island_position(rng, 0.65)
		var height := _get_terrain_height(pos.x, pos.z)
		if height < -1.0:
			continue
		pos.y = height
		var plant := _create_glow_plant(rng)
		plant.position = pos
		add_child(plant)


func _random_island_position(rng: RandomNumberGenerator, max_radius_frac: float) -> Vector3:
	var angle := rng.randf() * TAU
	var radius := rng.randf() * ISLAND_RADIUS * max_radius_frac
	return Vector3(cos(angle) * radius, 0.0, sin(angle) * radius)


func _get_terrain_height(x: float, z: float) -> float:
	var dist := Vector2(x, z).length() / ISLAND_RADIUS
	var mask := clamp(1.0 - dist * dist, 0.0, 1.0)
	mask = mask * mask
	var h := _noise.get_noise_2d(x, z) * TERRAIN_HEIGHT * mask
	h += sin(x * 0.1) * cos(z * 0.12) * 1.5 * mask
	if dist > 0.85:
		var cliff := (dist - 0.85) / 0.15
		h -= cliff * cliff * CLIFF_DROP
	return h


func _create_rock(rng: RandomNumberGenerator) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	var sz := rng.randf_range(0.3, 1.2)
	box.size = Vector3(sz, sz * rng.randf_range(0.4, 0.8), sz * rng.randf_range(0.7, 1.3))
	mesh.mesh = box
	mesh.rotation.x = rng.randf_range(-0.15, 0.15)
	mesh.rotation.z = rng.randf_range(-0.15, 0.15)

	var mat := StandardMaterial3D.new()
	var grey := rng.randf_range(0.15, 0.3)
	mat.albedo_color = Color(grey, grey * 0.95, grey * 0.9)
	mat.roughness = 0.9
	mesh.material_override = mat
	return mesh


func _create_crystal(rng: RandomNumberGenerator) -> Node3D:
	var root := Node3D.new()
	var height := rng.randf_range(1.0, 2.5)

	# Crystal body — elongated prism (cylinder as approximation)
	var body := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.05
	cyl.bottom_radius = rng.randf_range(0.15, 0.3)
	cyl.height = height
	cyl.radial_segments = 6  # Hexagonal cross-section
	body.mesh = cyl
	body.position.y = height * 0.5
	body.rotation.x = rng.randf_range(-0.1, 0.1)
	body.rotation.z = rng.randf_range(-0.1, 0.1)

	var mat := StandardMaterial3D.new()
	var hue := rng.randf_range(0.55, 0.7)  # Blue-purple range
	mat.albedo_color = Color.from_hsv(hue, 0.5, 0.7)
	mat.emission_enabled = true
	mat.emission = Color.from_hsv(hue, 0.6, 0.9)
	mat.emission_energy_multiplier = 1.5
	mat.metallic = 0.3
	mat.roughness = 0.2
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color.a = 0.85
	body.material_override = mat
	root.add_child(body)

	# Point light at crystal tip
	var light := OmniLight3D.new()
	light.light_color = Color.from_hsv(hue, 0.5, 1.0)
	light.light_energy = 0.8
	light.omni_range = 3.0
	light.omni_attenuation = 2.0
	light.position.y = height
	root.add_child(light)

	return root


func _create_glow_plant(rng: RandomNumberGenerator) -> Node3D:
	var root := Node3D.new()

	# Stem
	var stem := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	var h := rng.randf_range(0.3, 0.8)
	cyl.top_radius = 0.02
	cyl.bottom_radius = 0.04
	cyl.height = h
	stem.mesh = cyl
	stem.position.y = h * 0.5

	var stem_mat := StandardMaterial3D.new()
	stem_mat.albedo_color = Color(0.1, 0.25, 0.1)
	stem.material_override = stem_mat
	root.add_child(stem)

	# Glowing bulb at top
	var bulb := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = rng.randf_range(0.08, 0.15)
	sphere.height = sphere.radius * 2.0
	bulb.mesh = sphere
	bulb.position.y = h

	var bulb_mat := StandardMaterial3D.new()
	var plant_hue := rng.randf_range(0.25, 0.45)  # Green-cyan range
	bulb_mat.albedo_color = Color.from_hsv(plant_hue, 0.6, 0.8)
	bulb_mat.emission_enabled = true
	bulb_mat.emission = Color.from_hsv(plant_hue, 0.7, 1.0)
	bulb_mat.emission_energy_multiplier = 2.0
	bulb.material_override = bulb_mat
	root.add_child(bulb)

	return root


func _build_edge_particles() -> void:
	# Mystical particles floating up from the island edges
	var particles := GPUParticles3D.new()
	particles.name = "EdgeMist"

	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0.0, 1.0, 0.0)
	mat.spread = 15.0
	mat.initial_velocity_min = 0.3
	mat.initial_velocity_max = 1.0
	mat.gravity = Vector3(0.0, 0.2, 0.0)
	mat.damping_min = 0.5
	mat.damping_max = 1.0

	# Emit from a large ring shape at the island edge
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_RING
	mat.emission_ring_radius = ISLAND_RADIUS * 0.85
	mat.emission_ring_inner_radius = ISLAND_RADIUS * 0.7
	mat.emission_ring_height = 0.5
	mat.emission_ring_axis = Vector3(0.0, 1.0, 0.0)

	# Scale down over lifetime
	mat.scale_min = 0.1
	mat.scale_max = 0.25

	# Gentle blue-white color
	mat.color = Color(0.4, 0.6, 1.0, 0.4)

	particles.process_material = mat
	particles.amount = 50
	particles.lifetime = 4.0
	particles.randomness = 0.3
	particles.visibility_aabb = AABB(Vector3(-50, -10, -50), Vector3(100, 30, 100))
	particles.position.y = -2.0

	# Use small sphere as particle mesh
	var draw_mesh := SphereMesh.new()
	draw_mesh.radius = 0.08
	draw_mesh.height = 0.16
	particles.draw_pass_1 = draw_mesh

	add_child(particles)
