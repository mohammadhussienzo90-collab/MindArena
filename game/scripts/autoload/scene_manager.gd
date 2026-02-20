extends Node
## Scene transition manager. Autoload singleton.

signal scene_loading(progress: float)
signal scene_loaded(scene_name: String)

var current_scene_name: String = ""
var _transition_in_progress := false

const SCENES := {
	"login": "res://scenes/login.tscn",
	"main": "res://scenes/main.tscn",
	"world_hub": "res://scenes/world_hub.tscn",
	"assessment": "res://scenes/assessment.tscn",
	"challenge": "res://scenes/challenge.tscn",
	"feed": "res://scenes/feed.tscn",
	"chat": "res://scenes/chat.tscn",
	"profile": "res://scenes/profile.tscn",
	"settings": "res://scenes/settings.tscn",
	"arena": "res://scenes/arena.tscn",
	"friends": "res://scenes/friends.tscn",
}


func goto_scene(scene_key: String) -> void:
	if _transition_in_progress:
		return
	if not SCENES.has(scene_key):
		push_error("[SceneManager] Unknown scene: %s" % scene_key)
		return

	_transition_in_progress = true
	var scene_path = SCENES[scene_key]

	var new_scene = load(scene_path)
	if new_scene:
		get_tree().change_scene_to_packed(new_scene)
		current_scene_name = scene_key
		scene_loaded.emit(scene_key)
		print("[SceneManager] Loaded: %s" % scene_key)
	else:
		push_error("[SceneManager] Failed to load: %s" % scene_path)

	_transition_in_progress = false


func reload_current_scene() -> void:
	if current_scene_name != "":
		goto_scene(current_scene_name)
