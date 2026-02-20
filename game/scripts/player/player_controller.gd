extends CharacterBody3D
## First/third person player controller for MindArena world.

@export var speed := 5.0
@export var sprint_multiplier := 1.8
@export var jump_velocity := 4.5
@export var mouse_sensitivity := 0.003

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var _is_sprinting := false
var _nearby_portal: Node3D = null

@onready var camera_pivot: Node3D = $CameraPivot
@onready var camera: Camera3D = $CameraPivot/Camera3D
@onready var interaction_label: Label3D = $InteractionLabel if has_node("InteractionLabel") else null


func _ready() -> void:
	add_to_group("player")
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	if interaction_label:
		interaction_label.visible = false


func _unhandled_input(event: InputEvent) -> void:
	# Mouse look
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * mouse_sensitivity)
		camera_pivot.rotate_x(-event.relative.y * mouse_sensitivity)
		camera_pivot.rotation.x = clamp(
			camera_pivot.rotation.x,
			deg_to_rad(-89),
			deg_to_rad(89)
		)

	# Interact with nearby portal (E key)
	if event.is_action_pressed("interact") and _nearby_portal:
		_nearby_portal._enter_realm()

	# Toggle mouse capture
	if event.is_action_pressed("menu"):
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		else:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _physics_process(delta: float) -> void:
	# Gravity
	if not is_on_floor():
		velocity.y -= gravity * delta

	# Jump
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	# Sprint
	_is_sprinting = Input.is_action_pressed("sprint")

	# Movement
	var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()

	var current_speed = speed * (sprint_multiplier if _is_sprinting else 1.0)

	if direction:
		velocity.x = direction.x * current_speed
		velocity.z = direction.z * current_speed
	else:
		velocity.x = move_toward(velocity.x, 0, current_speed)
		velocity.z = move_toward(velocity.z, 0, current_speed)

	move_and_slide()


func set_nearby_portal(portal: Node3D) -> void:
	_nearby_portal = portal
	if interaction_label:
		interaction_label.visible = true
		var realm_name = portal.realm_display_name if "realm_display_name" in portal else ""
		interaction_label.text = "Press E — %s" % realm_name if realm_name != "" else "Press E to enter"


func clear_nearby_portal(portal: Node3D) -> void:
	if _nearby_portal == portal:
		_nearby_portal = null
		if interaction_label:
			interaction_label.visible = false
