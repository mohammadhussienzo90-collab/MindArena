extends CharacterBody3D
## First/third person player controller for MindArena world.
## Integrates with AvatarBuilder for visual representation and NoorVisual as companion.

@export var speed := 5.0
@export var sprint_multiplier := 1.8
@export var jump_velocity := 4.5
@export var mouse_sensitivity := 0.003

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var _is_sprinting := false
var _nearby_portal: Node3D = null

# Visual components
var avatar: AvatarBuilder
var avatar_animator: AvatarAnimator
var noor: NoorVisual

@onready var camera_pivot: Node3D = $CameraPivot
@onready var camera: Camera3D = $CameraPivot/Camera3D


func _ready() -> void:
	add_to_group("player")
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_build_avatar()
	_build_noor()


func _build_avatar() -> void:
	avatar = AvatarBuilder.new()
	avatar.name = "Avatar"

	# Apply colors from player profile if available
	var colors: Dictionary = PlayerData.get_avatar_colors()
	if colors.size() > 0:
		avatar.apply_colors(colors)

	add_child(avatar)

	# Setup animator
	avatar_animator = AvatarAnimator.new()
	avatar_animator.name = "AvatarAnimator"
	add_child(avatar_animator)
	avatar_animator.setup(avatar)


func _build_noor() -> void:
	noor = NoorVisual.new()
	noor.name = "NoorCompanion"
	# Add to parent scene (not player) so it doesn't inherit player rotation
	call_deferred("_attach_noor")


func _attach_noor() -> void:
	if get_parent():
		get_parent().add_child(noor)
		noor.set_target(self)


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
		if avatar_animator:
			avatar_animator.animate_portal_enter()
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

	# Update avatar animation
	if avatar_animator:
		avatar_animator.update_movement(velocity)


func set_nearby_portal(portal: Node3D) -> void:
	_nearby_portal = portal


func clear_nearby_portal(portal: Node3D) -> void:
	if _nearby_portal == portal:
		_nearby_portal = null
