extends Node
## Scene transition manager with fade effects. Autoload singleton.

signal scene_loaded(scene_name: String)

var current_scene_name: String = ""
var _transition_in_progress := false
var _overlay: ColorRect

const FADE_DURATION := 0.4

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

# Realm-specific transition colors for immersive effect
const REALM_TRANSITION_COLORS := {
	"logic_fortress": Color(0.1, 0.2, 0.5),
	"emotion_ocean": Color(0.0, 0.3, 0.35),
	"creativity_nebula": Color(0.3, 0.1, 0.4),
	"discipline_citadel": Color(0.4, 0.25, 0.05),
	"knowledge_peaks": Color(0.05, 0.25, 0.1),
	"social_bridge": Color(0.4, 0.2, 0.05),
	"wealth_garden": Color(0.05, 0.25, 0.1),
	"wellness_grove": Color(0.25, 0.1, 0.2),
}


func goto_scene(scene_key: String, transition_color: Color = Color.BLACK) -> void:
	if _transition_in_progress:
		return
	if not SCENES.has(scene_key):
		push_error("[SceneManager] Unknown scene: %s" % scene_key)
		return

	_transition_in_progress = true
	await _fade_out(transition_color)

	var scene_path: String = SCENES[scene_key]
	var new_scene := load(scene_path) as PackedScene
	if new_scene:
		get_tree().change_scene_to_packed(new_scene)
		current_scene_name = scene_key
		scene_loaded.emit(scene_key)
		print("[SceneManager] Loaded: %s" % scene_key)
	else:
		push_error("[SceneManager] Failed to load: %s" % scene_path)

	# Wait a frame for the new scene to initialize
	await get_tree().process_frame

	await _fade_in()
	_transition_in_progress = false


func goto_realm(realm_slug: String) -> void:
	"""Transition to a realm's challenge scene with realm-colored fade."""
	var color: Color = REALM_TRANSITION_COLORS.get(realm_slug, Color.BLACK)
	await goto_scene("challenge", color)


func goto_hub(from_realm: String = "") -> void:
	"""Return to world hub with appropriate transition."""
	var color: Color = REALM_TRANSITION_COLORS.get(from_realm, Color.BLACK)
	await goto_scene("world_hub", color)


func reload_current_scene() -> void:
	if current_scene_name != "":
		await goto_scene(current_scene_name)


func _fade_out(color: Color) -> void:
	_ensure_overlay()
	_overlay.color = Color(color, 0.0)
	_overlay.visible = true

	var tween := create_tween()
	tween.tween_property(_overlay, "color:a", 1.0, FADE_DURATION).set_trans(Tween.TRANS_CUBIC)
	await tween.finished


func _fade_in() -> void:
	_ensure_overlay()

	var tween := create_tween()
	tween.tween_property(_overlay, "color:a", 0.0, FADE_DURATION).set_trans(Tween.TRANS_CUBIC)
	await tween.finished
	_overlay.visible = false


func _ensure_overlay() -> void:
	if _overlay and is_instance_valid(_overlay):
		return

	# Create a CanvasLayer + ColorRect that persists across scene changes
	var canvas := CanvasLayer.new()
	canvas.name = "TransitionLayer"
	canvas.layer = 100  # Above everything
	add_child(canvas)

	_overlay = ColorRect.new()
	_overlay.name = "FadeOverlay"
	_overlay.color = Color(0, 0, 0, 0)
	_overlay.anchors_preset = Control.PRESET_FULL_RECT
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.visible = false
	canvas.add_child(_overlay)
