extends Area3D
## Portal to enter a realm. Placed in the world hub.

@export var realm_slug: String = ""
@export var realm_display_name: String = ""
@export var portal_color: Color = Color.WHITE

var _player_nearby := false

@onready var mesh: MeshInstance3D = $MeshInstance3D
@onready var label: Label3D = $Label3D


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	_update_visual_stage()

	if label:
		label.text = realm_display_name

	if mesh and mesh.get_surface_override_material(0):
		var mat = mesh.get_surface_override_material(0).duplicate()
		mat.albedo_color = portal_color
		mat.emission = portal_color
		mat.emission_energy_multiplier = 2.0
		mesh.set_surface_override_material(0, mat)


func _update_visual_stage() -> void:
	var stage = PlayerData.get_realm_visual_stage(realm_slug)
	var base_scale = 1.0 + (stage * 0.2)
	scale = Vector3(base_scale, base_scale, base_scale)


func _unhandled_input(event: InputEvent) -> void:
	if _player_nearby and event.is_action_pressed("interact"):
		_enter_realm()


func _enter_realm() -> void:
	GameManager.enter_realm(realm_slug)
	print("[Portal] Entering realm: %s" % realm_slug)


func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("player"):
		_player_nearby = true


func _on_body_exited(body: Node3D) -> void:
	if body.is_in_group("player"):
		_player_nearby = false
