extends Node3D
class_name RealmGenerator
## Procedural realm environment generator.
## Builds 8 distinct realm environments from primitives + shaders.
## Each realm scales with visual_stage (1 = bare, 5 = fully alive).
## No external assets needed — everything is generated from code.

const REALM_EXTENT := 40.0  # Half-size of the realm area


static func generate(realm_slug: String, visual_stage: int) -> Node3D:
	"""Generate a complete realm environment node."""
	var root := Node3D.new()
	root.name = "RealmEnvironment_%s" % realm_slug

	match realm_slug:
		"logic_fortress":
			_build_logic_fortress(root, visual_stage)
		"emotion_ocean":
			_build_emotion_ocean(root, visual_stage)
		"creativity_nebula":
			_build_creativity_nebula(root, visual_stage)
		"discipline_citadel":
			_build_discipline_citadel(root, visual_stage)
		"knowledge_peaks":
			_build_knowledge_peaks(root, visual_stage)
		"social_bridge":
			_build_social_bridge(root, visual_stage)
		"wealth_garden":
			_build_wealth_garden(root, visual_stage)
		"wellness_grove":
			_build_wellness_grove(root, visual_stage)
		_:
			_build_default(root, visual_stage)

	return root


# ==========================================================================
# LOGIC FORTRESS — Hexagonal grid, crystal pillars, light bridges
# ==========================================================================

static func _build_logic_fortress(root: Node3D, stage: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 101

	# Hexagonal floor grid
	var color := Color(0.15, 0.2, 0.4)
	for x in range(-6, 7):
		for z in range(-6, 7):
			var offset_x := float(x) * 2.5 + (1.25 if z % 2 != 0 else 0.0)
			var offset_z := float(z) * 2.2
			if Vector2(offset_x, offset_z).length() > REALM_EXTENT * 0.7:
				continue
			var hex := _create_hex_column(offset_x, offset_z, rng.randf_range(0.3, 1.0), color)
			root.add_child(hex)

	# Crystal pillars (more at higher stages)
	var crystal_count := 3 + stage * 3
	for i in range(crystal_count):
		var angle := float(i) / float(crystal_count) * TAU
		var dist := rng.randf_range(5.0, 15.0)
		var pos := Vector3(cos(angle) * dist, 0.0, sin(angle) * dist)
		var crystal := _create_crystal_pillar(pos, rng.randf_range(2.0, 5.0 + stage), Color(0.2, 0.4, 1.0))
		root.add_child(crystal)

	# Light bridges between pillars (stage >= 2)
	if stage >= 2:
		for i in range(min(stage * 2, 8)):
			var a_angle := rng.randf() * TAU
			var b_angle := a_angle + rng.randf_range(0.5, 1.5)
			var a_pos := Vector3(cos(a_angle) * 8.0, 2.0, sin(a_angle) * 8.0)
			var b_pos := Vector3(cos(b_angle) * 8.0, 2.0, sin(b_angle) * 8.0)
			var bridge := _create_light_bridge(a_pos, b_pos, Color(0.3, 0.5, 1.0))
			root.add_child(bridge)

	# Floating geometric shapes (stage >= 3)
	if stage >= 3:
		for i in range(stage * 2):
			var pos := Vector3(rng.randf_range(-12, 12), rng.randf_range(4, 10), rng.randf_range(-12, 12))
			var shape := _create_floating_shape(pos, rng, Color(0.2, 0.35, 0.9))
			root.add_child(shape)


# ==========================================================================
# EMOTION OCEAN — Water plane, floating lily pads, bioluminescent particles
# ==========================================================================

static func _build_emotion_ocean(root: Node3D, stage: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 202

	# Water plane
	var water := MeshInstance3D.new()
	water.name = "WaterSurface"
	var plane := PlaneMesh.new()
	plane.size = Vector2(80, 80)
	plane.subdivide_width = 32
	plane.subdivide_depth = 32
	water.mesh = plane
	water.position.y = -0.5

	var water_mat := StandardMaterial3D.new()
	water_mat.albedo_color = Color(0.05, 0.2, 0.35, 0.7)
	water_mat.emission_enabled = true
	water_mat.emission = Color(0.0, 0.15, 0.25)
	water_mat.emission_energy_multiplier = 0.5
	water_mat.metallic = 0.4
	water_mat.roughness = 0.1
	water_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	water.material_override = water_mat

	# Add collision for walking on lily pads
	var water_body := StaticBody3D.new()
	var water_col := CollisionShape3D.new()
	var water_shape := BoxShape3D.new()
	water_shape.size = Vector3(80, 0.1, 80)
	water_col.shape = water_shape
	water_body.add_child(water_col)
	water_body.position.y = -0.5
	root.add_child(water_body)
	root.add_child(water)

	# Floating lily pads (walkable platforms)
	var pad_count := 8 + stage * 3
	for i in range(pad_count):
		var pos := Vector3(rng.randf_range(-20, 20), 0.0, rng.randf_range(-20, 20))
		var pad := _create_lily_pad(pos, rng.randf_range(1.5, 3.0))
		root.add_child(pad)

	# Coral formations (stage >= 2)
	if stage >= 2:
		for i in range(stage * 3):
			var pos := Vector3(rng.randf_range(-15, 15), -0.3, rng.randf_range(-15, 15))
			var coral := _create_coral(pos, rng, Color(0.0, 0.6, 0.7))
			root.add_child(coral)

	# Bioluminescent particles (stage >= 3)
	if stage >= 3:
		var particles := _create_ambient_particles(
			Color(0.0, 0.8, 0.9, 0.4), 40 + stage * 10, Vector3(0, 2, 0)
		)
		root.add_child(particles)


# ==========================================================================
# CREATIVITY NEBULA — Floating platforms, color-shifting, abstract sculptures
# ==========================================================================

static func _build_creativity_nebula(root: Node3D, stage: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 303

	# Floating platforms at various heights
	var platform_count := 6 + stage * 2
	for i in range(platform_count):
		var pos := Vector3(
			rng.randf_range(-18, 18),
			rng.randf_range(-1, 6),
			rng.randf_range(-18, 18),
		)
		var size := rng.randf_range(2.0, 5.0)
		var hue := fmod(float(i) / float(platform_count), 1.0)
		var platform := _create_floating_platform(pos, size, Color.from_hsv(hue, 0.6, 0.8))
		root.add_child(platform)

	# Abstract sculptures (stage >= 2)
	if stage >= 2:
		for i in range(stage * 2):
			var pos := Vector3(rng.randf_range(-10, 10), rng.randf_range(1, 4), rng.randf_range(-10, 10))
			var sculpture := _create_abstract_sculpture(pos, rng)
			root.add_child(sculpture)

	# Paint splatter particles
	var splatter := _create_ambient_particles(
		Color(0.7, 0.2, 0.9, 0.5), 30 + stage * 8, Vector3(0, 3, 0)
	)
	root.add_child(splatter)


# ==========================================================================
# DISCIPLINE CITADEL — Fortress walls, training grounds
# ==========================================================================

static func _build_discipline_citadel(root: Node3D, stage: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 404

	# Stone floor
	var floor_mesh := _create_floor(Color(0.25, 0.2, 0.15), 60.0)
	root.add_child(floor_mesh)

	# Fortress walls in a ring
	var wall_count := 8 + stage * 2
	var ring_radius := 18.0
	for i in range(wall_count):
		var angle := float(i) / float(wall_count) * TAU
		var pos := Vector3(cos(angle) * ring_radius, 0, sin(angle) * ring_radius)
		var wall := _create_wall_segment(pos, angle, rng.randf_range(3.0, 5.0 + stage), Color(0.4, 0.3, 0.15))
		root.add_child(wall)

	# Training obstacle pillars
	for i in range(4 + stage):
		var pos := Vector3(rng.randf_range(-8, 8), 0, rng.randf_range(-8, 8))
		var pillar := _create_training_pillar(pos, rng.randf_range(1.5, 3.0))
		root.add_child(pillar)

	# Torch lights (stage >= 2)
	if stage >= 2:
		for i in range(wall_count / 2):
			var angle := float(i * 2) / float(wall_count) * TAU
			var pos := Vector3(cos(angle) * (ring_radius - 1), 3.0, sin(angle) * (ring_radius - 1))
			var torch := _create_torch(pos, Color(0.9, 0.5, 0.1))
			root.add_child(torch)


# ==========================================================================
# KNOWLEDGE PEAKS — Mountain terrain, book stacks, observatory
# ==========================================================================

static func _build_knowledge_peaks(root: Node3D, stage: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 505

	# Mountainous floor
	var floor_mesh := _create_floor(Color(0.2, 0.3, 0.15), 60.0)
	root.add_child(floor_mesh)

	# Mountain peaks
	for i in range(5 + stage):
		var pos := Vector3(rng.randf_range(-25, 25), 0, rng.randf_range(-25, 25))
		if pos.length() < 8:
			pos = pos.normalized() * 12
		var peak := _create_mountain_peak(pos, rng.randf_range(4, 10 + stage), rng)
		root.add_child(peak)

	# Book stack props (stage >= 2)
	if stage >= 2:
		for i in range(stage * 3):
			var pos := Vector3(rng.randf_range(-6, 6), 0, rng.randf_range(-6, 6))
			var books := _create_book_stack(pos, rng)
			root.add_child(books)

	# Observatory dome (stage >= 3)
	if stage >= 3:
		var dome := _create_observatory(Vector3(0, 0, -8))
		root.add_child(dome)

	# Floating knowledge particles
	var particles := _create_ambient_particles(
		Color(0.1, 0.8, 0.3, 0.4), 20 + stage * 5, Vector3(0, 5, 0)
	)
	root.add_child(particles)


# ==========================================================================
# SOCIAL BRIDGE — Bridge platforms, gathering areas
# ==========================================================================

static func _build_social_bridge(root: Node3D, stage: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 606

	# Central gathering platform
	var center := _create_floating_platform(Vector3.ZERO, 8.0, Color(0.8, 0.5, 0.2))
	root.add_child(center)

	# Bridge paths extending outward
	var bridge_count := 4 + stage
	for i in range(bridge_count):
		var angle := float(i) / float(bridge_count) * TAU
		for seg in range(3 + stage):
			var dist := 10.0 + seg * 4.0
			var pos := Vector3(cos(angle) * dist, rng.randf_range(-0.5, 0.5), sin(angle) * dist)
			var bridge_seg := _create_floating_platform(pos, 3.0, Color(0.7, 0.4, 0.15))
			root.add_child(bridge_seg)

		# Island at end of bridge
		var end_dist := 10.0 + (3 + stage) * 4.0
		var island_pos := Vector3(cos(angle) * end_dist, 0, sin(angle) * end_dist)
		var island := _create_floating_platform(island_pos, 5.0, Color(0.9, 0.6, 0.2))
		root.add_child(island)

	# Warm glow particles
	var particles := _create_ambient_particles(
		Color(1.0, 0.6, 0.2, 0.3), 25 + stage * 5, Vector3(0, 2, 0)
	)
	root.add_child(particles)


# ==========================================================================
# WEALTH GARDEN — Garden plots, crystal trees, fountain
# ==========================================================================

static func _build_wealth_garden(root: Node3D, stage: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 707

	# Lush green floor
	var floor_mesh := _create_floor(Color(0.15, 0.35, 0.12), 50.0)
	root.add_child(floor_mesh)

	# Garden plots in a grid
	for x in range(-2, 3):
		for z in range(-2, 3):
			if x == 0 and z == 0:
				continue  # Leave center for fountain
			var pos := Vector3(x * 6.0, 0.01, z * 6.0)
			var plot := _create_garden_plot(pos, rng, stage)
			root.add_child(plot)

	# Central fountain (stage >= 2)
	if stage >= 2:
		var fountain := _create_fountain(Vector3.ZERO)
		root.add_child(fountain)

	# Crystal trees (stage >= 3)
	if stage >= 3:
		for i in range(stage * 2):
			var angle := rng.randf() * TAU
			var dist := rng.randf_range(12, 20)
			var pos := Vector3(cos(angle) * dist, 0, sin(angle) * dist)
			var tree := _create_crystal_tree(pos, rng)
			root.add_child(tree)

	# Golden sparkle particles
	var particles := _create_ambient_particles(
		Color(0.9, 0.8, 0.2, 0.3), 20 + stage * 5, Vector3(0, 1.5, 0)
	)
	root.add_child(particles)


# ==========================================================================
# WELLNESS GROVE — Organic terrain, glowing mushrooms, zen garden
# ==========================================================================

static func _build_wellness_grove(root: Node3D, stage: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 808

	# Soft organic floor
	var floor_mesh := _create_floor(Color(0.2, 0.28, 0.18), 50.0)
	root.add_child(floor_mesh)

	# Glowing mushrooms
	var shroom_count := 8 + stage * 4
	for i in range(shroom_count):
		var pos := Vector3(rng.randf_range(-18, 18), 0, rng.randf_range(-18, 18))
		var shroom := _create_glowing_mushroom(pos, rng)
		root.add_child(shroom)

	# Zen stone circles (stage >= 2)
	if stage >= 2:
		_create_zen_circle(root, Vector3(0, 0, 0), 5.0, rng)

	# Meditation platforms (stage >= 3)
	if stage >= 3:
		for i in range(3):
			var angle := float(i) / 3.0 * TAU
			var pos := Vector3(cos(angle) * 10, 0.3, sin(angle) * 10)
			var platform := _create_floating_platform(pos, 3.0, Color(0.35, 0.25, 0.4))
			root.add_child(platform)

	# Peaceful particles
	var particles := _create_ambient_particles(
		Color(0.7, 0.3, 0.6, 0.3), 30 + stage * 5, Vector3(0, 2, 0)
	)
	root.add_child(particles)


# ==========================================================================
# DEFAULT fallback
# ==========================================================================

static func _build_default(root: Node3D, stage: int) -> void:
	var floor_mesh := _create_floor(Color(0.2, 0.2, 0.2), 50.0)
	root.add_child(floor_mesh)


# ==========================================================================
# SHARED BUILDING BLOCKS
# ==========================================================================

static func _create_hex_column(x: float, z: float, height: float, color: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 1.0
	cyl.bottom_radius = 1.0
	cyl.height = height
	cyl.radial_segments = 6
	mesh.mesh = cyl
	mesh.position = Vector3(x, height * 0.5, z)
	mesh.material_override = _make_mat(color, 0.3)
	return mesh


static func _create_crystal_pillar(pos: Vector3, height: float, color: Color) -> Node3D:
	var root := Node3D.new()
	var mesh := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.1
	cyl.bottom_radius = 0.4
	cyl.height = height
	cyl.radial_segments = 6
	mesh.mesh = cyl
	mesh.position = pos + Vector3(0, height * 0.5, 0)
	mesh.material_override = _make_mat(color, 2.0, 0.3, 0.2)
	root.add_child(mesh)

	var light := OmniLight3D.new()
	light.light_color = color
	light.light_energy = 1.0
	light.omni_range = 4.0
	light.position = pos + Vector3(0, height, 0)
	root.add_child(light)
	return root


static func _create_light_bridge(from_pos: Vector3, to_pos: Vector3, color: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var length := from_pos.distance_to(to_pos)
	var box := BoxMesh.new()
	box.size = Vector3(0.3, 0.1, length)
	mesh.mesh = box
	mesh.position = (from_pos + to_pos) * 0.5
	mesh.look_at(to_pos, Vector3.UP)
	mesh.material_override = _make_mat(color, 3.0, 0.5, 0.0)
	return mesh


static func _create_floating_shape(pos: Vector3, rng: RandomNumberGenerator, color: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var shape_type := rng.randi() % 3
	match shape_type:
		0:
			var box := BoxMesh.new()
			box.size = Vector3.ONE * rng.randf_range(0.3, 0.8)
			mesh.mesh = box
		1:
			var sphere := SphereMesh.new()
			sphere.radius = rng.randf_range(0.2, 0.5)
			sphere.height = sphere.radius * 2
			mesh.mesh = sphere
		2:
			var cyl := CylinderMesh.new()
			cyl.top_radius = 0.0
			cyl.bottom_radius = rng.randf_range(0.2, 0.5)
			cyl.height = rng.randf_range(0.5, 1.0)
			mesh.mesh = cyl
	mesh.position = pos
	mesh.rotation = Vector3(rng.randf() * TAU, rng.randf() * TAU, rng.randf() * TAU)
	mesh.material_override = _make_mat(color, 1.5)
	return mesh


static func _create_lily_pad(pos: Vector3, size: float) -> Node3D:
	var root := Node3D.new()
	var mesh := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = size
	cyl.bottom_radius = size * 0.9
	cyl.height = 0.15
	cyl.radial_segments = 12
	mesh.mesh = cyl
	mesh.position = pos + Vector3(0, 0.07, 0)
	mesh.material_override = _make_mat(Color(0.1, 0.4, 0.15), 0.3)
	root.add_child(mesh)

	# Walkable collision
	var body := StaticBody3D.new()
	var col := CollisionShape3D.new()
	var shape := CylinderShape3D.new()
	shape.radius = size * 0.9
	shape.height = 0.2
	col.shape = shape
	body.add_child(col)
	body.position = pos + Vector3(0, 0.1, 0)
	root.add_child(body)
	return root


static func _create_coral(pos: Vector3, rng: RandomNumberGenerator, color: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = rng.randf_range(0.05, 0.2)
	cyl.bottom_radius = rng.randf_range(0.2, 0.5)
	cyl.height = rng.randf_range(0.5, 2.0)
	mesh.mesh = cyl
	mesh.position = pos + Vector3(0, cyl.height * 0.5, 0)
	mesh.rotation.x = rng.randf_range(-0.2, 0.2)
	mesh.rotation.z = rng.randf_range(-0.2, 0.2)
	mesh.material_override = _make_mat(color, 1.0)
	return mesh


static func _create_floating_platform(pos: Vector3, size: float, color: Color) -> Node3D:
	var root := Node3D.new()
	var mesh := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = size
	cyl.bottom_radius = size * 0.8
	cyl.height = 0.6
	cyl.radial_segments = 8
	mesh.mesh = cyl
	mesh.position = pos
	mesh.material_override = _make_mat(color, 0.5)
	root.add_child(mesh)

	var body := StaticBody3D.new()
	var col := CollisionShape3D.new()
	var shape := CylinderShape3D.new()
	shape.radius = size
	shape.height = 0.7
	col.shape = shape
	body.add_child(col)
	body.position = pos
	root.add_child(body)
	return root


static func _create_abstract_sculpture(pos: Vector3, rng: RandomNumberGenerator) -> Node3D:
	var root := Node3D.new()
	var piece_count := rng.randi_range(3, 6)
	for i in range(piece_count):
		var mesh := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(rng.randf_range(0.2, 0.8), rng.randf_range(0.2, 1.5), rng.randf_range(0.2, 0.8))
		mesh.mesh = box
		mesh.position = pos + Vector3(rng.randf_range(-0.5, 0.5), float(i) * 0.4, rng.randf_range(-0.5, 0.5))
		mesh.rotation = Vector3(rng.randf() * 0.5, rng.randf() * TAU, rng.randf() * 0.5)
		var hue := fmod(float(i) / float(piece_count) + rng.randf() * 0.2, 1.0)
		mesh.material_override = _make_mat(Color.from_hsv(hue, 0.7, 0.8), 1.5)
		root.add_child(mesh)
	return root


static func _create_floor(color: Color, size: float) -> Node3D:
	var root := Node3D.new()
	var mesh := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(size, size)
	mesh.mesh = plane
	mesh.material_override = _make_mat(color, 0.0, 0.0, 0.9)
	root.add_child(mesh)

	var body := StaticBody3D.new()
	var col := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(size, 0.1, size)
	col.shape = shape
	body.add_child(col)
	root.add_child(body)
	return root


static func _create_wall_segment(pos: Vector3, angle: float, height: float, color: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(3.0, height, 0.8)
	mesh.mesh = box
	mesh.position = pos + Vector3(0, height * 0.5, 0)
	mesh.rotation.y = angle
	mesh.material_override = _make_mat(color, 0.0, 0.0, 0.85)
	return mesh


static func _create_training_pillar(pos: Vector3, height: float) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.3
	cyl.bottom_radius = 0.4
	cyl.height = height
	mesh.mesh = cyl
	mesh.position = pos + Vector3(0, height * 0.5, 0)
	mesh.material_override = _make_mat(Color(0.5, 0.35, 0.2), 0.0, 0.0, 0.8)
	return mesh


static func _create_torch(pos: Vector3, color: Color) -> Node3D:
	var root := Node3D.new()
	var light := OmniLight3D.new()
	light.light_color = color
	light.light_energy = 2.0
	light.omni_range = 6.0
	light.position = pos
	root.add_child(light)

	var flame := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.12
	sphere.height = 0.24
	flame.mesh = sphere
	flame.position = pos
	flame.material_override = _make_mat(color, 4.0)
	root.add_child(flame)
	return root


static func _create_mountain_peak(pos: Vector3, height: float, rng: RandomNumberGenerator) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.5
	cyl.bottom_radius = height * 0.6
	cyl.height = height
	cyl.radial_segments = 8
	mesh.mesh = cyl
	mesh.position = pos + Vector3(0, height * 0.5, 0)
	var grey := rng.randf_range(0.2, 0.35)
	mesh.material_override = _make_mat(Color(grey, grey + 0.05, grey - 0.02), 0.0, 0.0, 0.9)
	return mesh


static func _create_book_stack(pos: Vector3, rng: RandomNumberGenerator) -> Node3D:
	var root := Node3D.new()
	var count := rng.randi_range(2, 5)
	for i in range(count):
		var book := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(rng.randf_range(0.3, 0.6), 0.08, rng.randf_range(0.4, 0.7))
		book.mesh = box
		book.position = pos + Vector3(0, 0.04 + i * 0.09, 0)
		book.rotation.y = rng.randf_range(-0.2, 0.2)
		var hue := rng.randf()
		book.material_override = _make_mat(Color.from_hsv(hue, 0.5, 0.6), 0.0)
		root.add_child(book)
	return root


static func _create_observatory(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	# Base cylinder
	var base := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 3.0
	cyl.bottom_radius = 3.5
	cyl.height = 4.0
	base.mesh = cyl
	base.position = pos + Vector3(0, 2, 0)
	base.material_override = _make_mat(Color(0.3, 0.25, 0.2), 0.0, 0.0, 0.8)
	root.add_child(base)

	# Dome
	var dome := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 3.0
	sphere.height = 3.0
	sphere.is_hemisphere = true
	dome.mesh = sphere
	dome.position = pos + Vector3(0, 4, 0)
	dome.material_override = _make_mat(Color(0.2, 0.35, 0.25), 0.5, 0.3, 0.4)
	root.add_child(dome)
	return root


static func _create_garden_plot(pos: Vector3, rng: RandomNumberGenerator, stage: int) -> Node3D:
	var root := Node3D.new()
	# Plot border
	var border := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(4.0, 0.3, 4.0)
	border.mesh = box
	border.position = pos + Vector3(0, 0.15, 0)
	border.material_override = _make_mat(Color(0.25, 0.15, 0.08), 0.0)
	root.add_child(border)

	# Plants growing based on stage
	var plant_count := stage + 1
	for i in range(plant_count):
		var p_pos := pos + Vector3(rng.randf_range(-1.5, 1.5), 0.3, rng.randf_range(-1.5, 1.5))
		var stem := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		var h := rng.randf_range(0.3, 0.6 + stage * 0.2)
		cyl.top_radius = 0.03
		cyl.bottom_radius = 0.05
		cyl.height = h
		stem.mesh = cyl
		stem.position = p_pos + Vector3(0, h * 0.5, 0)
		stem.material_override = _make_mat(Color(0.1, 0.3, 0.1), 0.0)
		root.add_child(stem)
	return root


static func _create_fountain(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	# Base
	var base := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 2.5
	cyl.bottom_radius = 3.0
	cyl.height = 0.8
	base.mesh = cyl
	base.position = pos + Vector3(0, 0.4, 0)
	base.material_override = _make_mat(Color(0.3, 0.3, 0.3), 0.0, 0.0, 0.7)
	root.add_child(base)

	# Center pillar
	var pillar := MeshInstance3D.new()
	var pcyl := CylinderMesh.new()
	pcyl.top_radius = 0.3
	pcyl.bottom_radius = 0.5
	pcyl.height = 2.0
	pillar.mesh = pcyl
	pillar.position = pos + Vector3(0, 1.8, 0)
	pillar.material_override = _make_mat(Color(0.35, 0.35, 0.35), 0.0)
	root.add_child(pillar)

	# Water particles
	var particles := GPUParticles3D.new()
	particles.position = pos + Vector3(0, 3, 0)
	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0, 1, 0)
	mat.spread = 30.0
	mat.initial_velocity_min = 1.0
	mat.initial_velocity_max = 2.0
	mat.gravity = Vector3(0, -5, 0)
	mat.scale_min = 0.03
	mat.scale_max = 0.06
	mat.color = Color(0.3, 0.7, 1.0, 0.5)
	particles.process_material = mat
	particles.amount = 30
	particles.lifetime = 1.5
	var draw_mesh := SphereMesh.new()
	draw_mesh.radius = 0.04
	draw_mesh.height = 0.08
	particles.draw_pass_1 = draw_mesh
	root.add_child(particles)

	return root


static func _create_crystal_tree(pos: Vector3, rng: RandomNumberGenerator) -> Node3D:
	var root := Node3D.new()
	# Trunk
	var trunk := MeshInstance3D.new()
	var tcyl := CylinderMesh.new()
	var h := rng.randf_range(2.0, 4.0)
	tcyl.top_radius = 0.1
	tcyl.bottom_radius = 0.25
	tcyl.height = h
	trunk.mesh = tcyl
	trunk.position = pos + Vector3(0, h * 0.5, 0)
	trunk.material_override = _make_mat(Color(0.2, 0.15, 0.1), 0.0)
	root.add_child(trunk)

	# Crystal canopy
	for i in range(3):
		var crystal := MeshInstance3D.new()
		var ccyl := CylinderMesh.new()
		ccyl.top_radius = 0.0
		ccyl.bottom_radius = rng.randf_range(0.3, 0.6)
		ccyl.height = rng.randf_range(0.8, 1.5)
		ccyl.radial_segments = 6
		crystal.mesh = ccyl
		crystal.position = pos + Vector3(
			rng.randf_range(-0.3, 0.3), h + float(i) * 0.4,
			rng.randf_range(-0.3, 0.3)
		)
		crystal.rotation = Vector3(rng.randf_range(-0.3, 0.3), rng.randf() * TAU, rng.randf_range(-0.3, 0.3))
		var hue := rng.randf_range(0.25, 0.45)
		crystal.material_override = _make_mat(Color.from_hsv(hue, 0.5, 0.8), 2.0, 0.3, 0.2)
		root.add_child(crystal)
	return root


static func _create_glowing_mushroom(pos: Vector3, rng: RandomNumberGenerator) -> Node3D:
	var root := Node3D.new()

	# Stem
	var stem := MeshInstance3D.new()
	var scyl := CylinderMesh.new()
	var h := rng.randf_range(0.3, 1.2)
	scyl.top_radius = 0.06
	scyl.bottom_radius = 0.1
	scyl.height = h
	stem.mesh = scyl
	stem.position = pos + Vector3(0, h * 0.5, 0)
	stem.material_override = _make_mat(Color(0.25, 0.2, 0.3), 0.0)
	root.add_child(stem)

	# Cap
	var cap := MeshInstance3D.new()
	var ccyl := CylinderMesh.new()
	ccyl.top_radius = 0.01
	ccyl.bottom_radius = rng.randf_range(0.15, 0.4)
	ccyl.height = 0.15
	cap.mesh = ccyl
	cap.position = pos + Vector3(0, h + 0.07, 0)
	var hue := rng.randf_range(0.75, 0.95)  # Pink-magenta range
	cap.material_override = _make_mat(Color.from_hsv(hue, 0.6, 0.8), 2.5)
	root.add_child(cap)

	# Glow light
	var light := OmniLight3D.new()
	light.light_color = Color.from_hsv(hue, 0.5, 1.0)
	light.light_energy = 0.6
	light.omni_range = 2.5
	light.position = pos + Vector3(0, h + 0.1, 0)
	root.add_child(light)
	return root


static func _create_zen_circle(parent: Node3D, center: Vector3, radius: float, rng: RandomNumberGenerator) -> void:
	var stone_count := 8
	for i in range(stone_count):
		var angle := float(i) / float(stone_count) * TAU
		var pos := center + Vector3(cos(angle) * radius, 0, sin(angle) * radius)
		var stone := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = rng.randf_range(0.2, 0.5)
		sphere.height = sphere.radius * 1.5
		stone.mesh = sphere
		stone.position = pos + Vector3(0, sphere.radius * 0.5, 0)
		var grey := rng.randf_range(0.3, 0.5)
		stone.material_override = _make_mat(Color(grey, grey, grey), 0.0)
		parent.add_child(stone)


static func _create_ambient_particles(color: Color, amount: int, center: Vector3) -> GPUParticles3D:
	var particles := GPUParticles3D.new()
	particles.position = center
	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0, 0.5, 0)
	mat.spread = 180.0
	mat.initial_velocity_min = 0.1
	mat.initial_velocity_max = 0.5
	mat.gravity = Vector3(0, 0.1, 0)
	mat.damping_min = 0.5
	mat.damping_max = 1.5
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	mat.emission_box_extents = Vector3(15, 3, 15)
	mat.scale_min = 0.03
	mat.scale_max = 0.08
	mat.color = color
	particles.process_material = mat
	particles.amount = amount
	particles.lifetime = 4.0
	particles.randomness = 0.5
	particles.visibility_aabb = AABB(Vector3(-25, -5, -25), Vector3(50, 15, 50))
	var draw_mesh := SphereMesh.new()
	draw_mesh.radius = 0.04
	draw_mesh.height = 0.08
	particles.draw_pass_1 = draw_mesh
	return particles


static func _make_mat(color: Color, emission_strength: float = 0.0, metallic: float = 0.0, roughness: float = 0.65) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	if emission_strength > 0.01:
		mat.emission_enabled = true
		mat.emission = color
		mat.emission_energy_multiplier = emission_strength
	mat.metallic = metallic
	mat.roughness = roughness
	return mat
