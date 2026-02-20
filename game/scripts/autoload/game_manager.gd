extends Node
## Central game state manager. Autoload singleton.

signal state_changed(new_state: String)
signal realm_entered(realm_slug: String)
signal challenge_started(challenge_data: Dictionary)
signal challenge_completed(result: Dictionary)
signal xp_earned(amount: int, total: int)
signal level_up(new_level: int)
signal achievement_earned(achievement: Dictionary)
signal quest_completed(quest_data: Dictionary)

enum GameState { LOADING, MENU, WORLD, CHALLENGE, ASSESSMENT, FEED, CHAT, PAUSED }

var current_state: GameState = GameState.LOADING
var current_realm: String = ""
var is_initialized := false
var _notification_queue: Array = []


func _ready() -> void:
	print("[GameManager] Initializing...")


func change_state(new_state: GameState) -> void:
	var old_state = current_state
	current_state = new_state
	state_changed.emit(GameState.keys()[new_state])
	print("[GameManager] State: %s -> %s" % [GameState.keys()[old_state], GameState.keys()[new_state]])


func enter_realm(realm_slug: String) -> void:
	current_realm = realm_slug
	realm_entered.emit(realm_slug)
	change_state(GameState.CHALLENGE)
	SceneManager.goto_scene("challenge")
	print("[GameManager] Entered realm: %s" % realm_slug)


func start_challenge(challenge_data: Dictionary) -> void:
	change_state(GameState.CHALLENGE)
	challenge_started.emit(challenge_data)


func complete_challenge(result: Dictionary) -> void:
	challenge_completed.emit(result)
	var xp = result.get("base_xp", 0) + result.get("bonus_xp", 0)
	if xp > 0:
		PlayerData.total_xp += xp
		xp_earned.emit(xp, PlayerData.total_xp)

		# Check for level up
		var new_level = _calculate_level(PlayerData.total_xp)
		if new_level > PlayerData.overall_level:
			PlayerData.overall_level = new_level
			level_up.emit(new_level)

	# Check for newly earned achievements from server response
	var new_achievements = result.get("new_achievements", [])
	for ach in new_achievements:
		achievement_earned.emit(ach)

	PlayerData.data_updated.emit()


func return_to_world() -> void:
	change_state(GameState.WORLD)
	SceneManager.goto_scene("world_hub")


func initialize_game() -> void:
	if is_initialized:
		return
	print("[GameManager] Game initialized")
	is_initialized = true
	change_state(GameState.MENU)


func _calculate_level(total_xp: int) -> int:
	var level = 1
	while PlayerData.xp_for_level(level + 1) <= total_xp:
		level += 1
	return level
