extends Node3D
## Main scene entry controller.
## Handles initial game load: checks auth state and routes to the correct scene.

@onready var camera: Camera3D = $Camera3D


func _ready() -> void:
	GameManager.initialize_game()
	_route_player()


func _route_player() -> void:
	if not AuthManager.is_authenticated:
		SceneManager.goto_scene("login")
		return

	# Authenticated — load profile and decide where to go
	await PlayerData.load_profile()
	await PlayerData.load_realm_stats()

	if not PlayerData.onboarding_done:
		SceneManager.goto_scene("assessment")
	else:
		SceneManager.goto_scene("world_hub")
