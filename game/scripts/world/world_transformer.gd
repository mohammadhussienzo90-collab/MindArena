extends Node3D
## Transforms world visuals based on player progression.
## Attach to the world hub root. Updates environment and realm portals.

@export var base_environment: Environment

var _portal_nodes: Array = []


func _ready() -> void:
	PlayerData.data_updated.connect(_on_data_updated)
	# Defer finding portals to ensure scene tree is fully loaded
	call_deferred("_find_portals")


func _find_portals() -> void:
	# Search the entire scene tree for portal nodes with realm_slug
	var portals_parent = get_parent().get_node_or_null("Portals")
	if portals_parent:
		for child in portals_parent.get_children():
			if "realm_slug" in child and child.realm_slug != "":
				_portal_nodes.append(child)
	_apply_transformations()


func _on_data_updated() -> void:
	_apply_transformations()


func _apply_transformations() -> void:
	# Overall world brightness based on player level
	if base_environment:
		var level_factor = clamp(float(PlayerData.overall_level) / 50.0, 0.0, 1.0)
		base_environment.ambient_light_energy = 0.3 + (level_factor * 0.7)

	# Update each portal based on realm progress
	for portal in _portal_nodes:
		var stage = PlayerData.get_realm_visual_stage(portal.realm_slug)
		_apply_realm_stage(portal, stage)


func _apply_realm_stage(node: Node3D, stage: int) -> void:
	# Stage 0: Dim, barren
	# Stage 1: Some color appears
	# Stage 2: Flora/details grow
	# Stage 3: Rich environment
	# Stage 4: Spectacular effects
	# Stage 5: Fully transformed, glowing

	var intensity = float(stage) / 5.0

	# Scale portal based on progression
	var base_scale = 1.0 + (stage * 0.15)
	node.scale = Vector3(base_scale, base_scale, base_scale)

	# Show/hide detail nodes based on growth stage
	for child in node.get_children():
		if child.has_meta("growth_stage"):
			var required = child.get_meta("growth_stage")
			child.visible = stage >= required

	# Adjust lighting in realm area
	for light in node.find_children("*", "Light3D"):
		light.light_energy = 0.2 + (intensity * 1.8)
