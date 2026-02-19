extends Node3D
## Transforms world visuals based on player progression.
## Attach to the world hub root. Updates environment and realm portals.

@export var base_environment: Environment

var _realm_nodes: Dictionary = {}


func _ready() -> void:
	PlayerData.data_updated.connect(_on_data_updated)
	_find_realm_nodes()
	_apply_transformations()


func _find_realm_nodes() -> void:
	for child in get_children():
		if child.has_meta("realm_slug"):
			_realm_nodes[child.get_meta("realm_slug")] = child


func _on_data_updated() -> void:
	_apply_transformations()


func _apply_transformations() -> void:
	# Overall world brightness based on player level
	if base_environment:
		var level_factor = clamp(float(PlayerData.overall_level) / 50.0, 0.0, 1.0)
		base_environment.ambient_light_energy = 0.3 + (level_factor * 0.7)

	# Update each realm area
	for slug in _realm_nodes:
		var stage = PlayerData.get_realm_visual_stage(slug)
		_apply_realm_stage(_realm_nodes[slug], slug, stage)


func _apply_realm_stage(node: Node3D, _realm_slug: String, stage: int) -> void:
	# Stage 0: Dim, barren
	# Stage 1: Some color appears
	# Stage 2: Flora/details grow
	# Stage 3: Rich environment
	# Stage 4: Spectacular effects
	# Stage 5: Fully transformed, glowing

	var intensity = float(stage) / 5.0

	# Scale environmental details
	for child in node.get_children():
		if child.has_meta("growth_stage"):
			var required = child.get_meta("growth_stage")
			child.visible = stage >= required

	# Adjust lighting in realm area
	for light in node.find_children("*", "Light3D"):
		light.light_energy = 0.2 + (intensity * 1.8)
