extends Node
## Central game state manager. Autoload singleton.

signal state_changed(new_state: String)
signal realm_entered(realm_slug: String)
signal challenge_started(challenge_data: Dictionary)
signal challenge_completed(result: Dictionary)
signal xp_earned(amount: int, total: int)
signal level_up(new_level: int)

enum GameState { LOADING, MENU, WORLD, CHALLENGE, ASSESSMENT, FEED, CHAT, PAUSED }

var current_state: GameState = GameState.LOADING
var current_realm: String = ""
var is_initialized := false


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
	print("[GameManager] Entered realm: %s" % realm_slug)


func start_challenge(challenge_data: Dictionary) -> void:
	change_state(GameState.CHALLENGE)
	challenge_started.emit(challenge_data)


func complete_challenge(result: Dictionary) -> void:
	challenge_completed.emit(result)
	if result.get("xp_earned", 0) > 0:
		xp_earned.emit(result.xp_earned, PlayerData.total_xp)
	change_state(GameState.WORLD)


func initialize_game() -> void:
	if is_initialized:
		return
	print("[GameManager] Game initialized")
	is_initialized = true
	change_state(GameState.MENU)
