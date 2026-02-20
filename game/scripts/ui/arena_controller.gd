extends Control
## Arena PvP controller — matchmaking, live gameplay, results.

enum ArenaState { LOBBY, SEARCHING, WAITING, PLAYING, RESULTS }

var _state: ArenaState = ArenaState.LOBBY
var _current_match: Dictionary = {}
var _current_challenge: Dictionary = {}
var _round_start_time: float = 0.0
var _match_poll_timer: float = 0.0
var _player_stats: Dictionary = {}
var _selected_match_type: String = ""
var _option_buttons: Array[Button] = []
var _round_time_limit: float = 30.0
var _round_timer_active: bool = false

const POLL_INTERVAL: float = 3.0

@onready var status_label: Label = $StatusLabel if has_node("StatusLabel") else null
@onready var match_type_buttons: Container = $MatchTypeButtons if has_node("MatchTypeButtons") else null
@onready var realm_selector: Container = $RealmSelector if has_node("RealmSelector") else null
@onready var question_label: RichTextLabel = $QuestionLabel if has_node("QuestionLabel") else null
@onready var options_container: Container = $OptionsContainer if has_node("OptionsContainer") else null
@onready var timer_label: Label = $TimerLabel if has_node("TimerLabel") else null
@onready var score_label: Label = $ScoreLabel if has_node("ScoreLabel") else null
@onready var round_label: Label = $RoundLabel if has_node("RoundLabel") else null
@onready var result_container: Container = $ResultContainer if has_node("ResultContainer") else null
@onready var back_button: Button = $BackButton if has_node("BackButton") else null


func _ready() -> void:
	_load_stats()
	_show_lobby()
	if back_button:
		back_button.pressed.connect(_on_back_pressed)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

func _load_stats() -> void:
	print("[Arena] Loading player arena stats...")
	var result = await ApiClient.get("/arena/stats/")
	if result.status == 200 and result.data:
		_player_stats = result.data
		print("[Arena] Stats loaded — ELO: %d, Wins: %d, Losses: %d" % [
			_player_stats.get("elo_rating", 1000),
			_player_stats.get("wins", 0),
			_player_stats.get("losses", 0),
		])
	elif result.status == 0:
		print("[Arena] Could not load stats (offline)")
		if status_label:
			status_label.text = "Could not load stats — check your connection."
	else:
		print("[Arena] Stats request failed with status %d" % result.status)


# ---------------------------------------------------------------------------
# Lobby
# ---------------------------------------------------------------------------

func _show_lobby() -> void:
	_state = ArenaState.LOBBY
	_round_timer_active = false

	# Hide gameplay / result elements
	_set_visible(question_label, false)
	_set_visible(options_container, false)
	_set_visible(timer_label, false)
	_set_visible(round_label, false)
	_set_visible(result_container, false)
	_set_visible(realm_selector, false)

	# Show lobby elements
	_set_visible(match_type_buttons, true)
	_set_visible(score_label, true)
	_set_visible(back_button, true)

	# Display ELO and record
	if score_label:
		var elo = _player_stats.get("elo_rating", 1000)
		var wins = _player_stats.get("wins", 0)
		var losses = _player_stats.get("losses", 0)
		score_label.text = "ELO: %d  |  W: %d  L: %d" % [elo, wins, losses]

	if status_label:
		status_label.text = "Choose a match type"

	# Build match-type buttons if the container is empty
	if match_type_buttons and match_type_buttons.get_child_count() == 0:
		var types := ["speed", "strategic", "team"]
		var labels := ["Speed Match", "Strategic Match", "Team Battle"]
		for i in range(types.size()):
			var btn := Button.new()
			btn.text = labels[i]
			btn.add_theme_font_size_override("font_size", 18)
			btn.custom_minimum_size.y = 48
			btn.pressed.connect(_on_match_type_selected.bind(types[i]))
			match_type_buttons.add_child(btn)


# ---------------------------------------------------------------------------
# Match type selection
# ---------------------------------------------------------------------------

func _on_match_type_selected(match_type: String) -> void:
	_selected_match_type = match_type
	print("[Arena] Match type selected: %s" % match_type)

	if status_label:
		status_label.text = "Select a realm for %s match" % match_type.capitalize()

	_set_visible(match_type_buttons, false)
	_set_visible(realm_selector, true)

	# Populate realm selector if empty
	if realm_selector and realm_selector.get_child_count() == 0:
		_populate_realm_selector()


func _populate_realm_selector() -> void:
	if not realm_selector:
		return

	# Try loading realms from the API; fall back to cached realm_stats
	var result = await ApiClient.get("/realms/")
	if result.status == 200 and result.data:
		var realms: Array = result.data if result.data is Array else result.data.get("results", [])
		for realm in realms:
			var slug: String = realm.get("slug", "")
			var btn := Button.new()
			btn.text = _localized(realm, "name")
			btn.add_theme_font_size_override("font_size", 16)
			btn.custom_minimum_size.y = 44
			btn.pressed.connect(_on_realm_selected.bind(slug))
			realm_selector.add_child(btn)
	else:
		# Fallback: use cached PlayerData realm_stats keys
		for slug in PlayerData.realm_stats.keys():
			var btn := Button.new()
			btn.text = slug.capitalize()
			btn.add_theme_font_size_override("font_size", 16)
			btn.custom_minimum_size.y = 44
			btn.pressed.connect(_on_realm_selected.bind(slug))
			realm_selector.add_child(btn)


# ---------------------------------------------------------------------------
# Realm selection -> matchmaking
# ---------------------------------------------------------------------------

func _on_realm_selected(realm_slug: String) -> void:
	print("[Arena] Realm selected: %s" % realm_slug)
	_set_visible(realm_selector, false)
	_start_matchmaking(_selected_match_type, realm_slug)


func _start_matchmaking(match_type: String, realm_slug: String) -> void:
	_state = ArenaState.SEARCHING
	if status_label:
		status_label.text = "Searching for an opponent..."
	print("[Arena] Searching for %s match in %s..." % [match_type, realm_slug])

	# Step 1: Try to find an existing waiting match
	var find_result = await ApiClient.get(
		"/arena/matches/find/?match_type=%s&realm_slug=%s" % [match_type, realm_slug]
	)

	if find_result.status == 200 and find_result.data and find_result.data.get("id"):
		# Found an open match — join it
		var match_id: int = find_result.data.get("id", 0)
		print("[Arena] Found open match #%d, joining..." % match_id)
		var join_result = await ApiClient.post("/arena/matches/%d/join/" % match_id)
		if join_result.status in [200, 201] and join_result.data:
			_on_match_joined(join_result.data)
			return
		else:
			print("[Arena] Failed to join match #%d (status %d)" % [match_id, join_result.status])

	# Step 2: No open match found (or join failed) — create a new one
	print("[Arena] No open match found, creating new match...")
	var create_result = await ApiClient.post("/arena/matches/create/", {
		"match_type": match_type,
		"realm_slug": realm_slug,
		"total_rounds": 5,
	})

	if create_result.status in [200, 201] and create_result.data:
		_on_match_joined(create_result.data)
	elif create_result.status == 0:
		if status_label:
			status_label.text = "Connection error — could not create match."
		print("[Arena] Create match failed (offline)")
		_show_lobby()
	else:
		var detail = ""
		if create_result.data is Dictionary:
			detail = create_result.data.get("detail", create_result.data.get("error", ""))
		if status_label:
			status_label.text = "Could not create match: %s" % detail if detail != "" else "Could not create match (Error %d)." % create_result.status
		print("[Arena] Create match failed: status %d — %s" % [create_result.status, detail])
		_show_lobby()


# ---------------------------------------------------------------------------
# Match joined
# ---------------------------------------------------------------------------

func _on_match_joined(match_data: Dictionary) -> void:
	_current_match = match_data
	var match_status: String = match_data.get("status", "waiting")
	print("[Arena] Match #%d joined — status: %s" % [
		match_data.get("id", 0), match_status,
	])

	if match_status == "in_progress":
		# Both players present — start playing
		_state = ArenaState.PLAYING
		_start_round()
	else:
		# Waiting for an opponent
		_state = ArenaState.WAITING
		_match_poll_timer = 0.0
		if status_label:
			status_label.text = "Waiting for an opponent to join..."
		print("[Arena] Waiting for opponent (polling every %.0fs)..." % POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Polling (_process)
# ---------------------------------------------------------------------------

func _process(delta: float) -> void:
	# Poll for opponent while waiting
	if _state == ArenaState.WAITING:
		_match_poll_timer += delta
		if _match_poll_timer >= POLL_INTERVAL:
			_match_poll_timer = 0.0
			_poll_match_status()

	# Update round timer while playing
	if _state == ArenaState.PLAYING and _round_timer_active:
		var elapsed = Time.get_ticks_msec() / 1000.0 - _round_start_time
		var remaining = max(_round_time_limit - elapsed, 0.0)
		_update_timer(remaining)
		if remaining <= 0.0:
			_round_timer_active = false
			print("[Arena] Time expired for this round")
			_on_answer_selected(-1)  # auto-submit with no answer


func _poll_match_status() -> void:
	var match_id: int = _current_match.get("id", 0)
	if match_id == 0:
		return

	var result = await ApiClient.get("/arena/matches/%d/" % match_id)
	if result.status == 200 and result.data:
		_current_match = result.data
		var match_status: String = result.data.get("status", "waiting")
		if match_status == "in_progress":
			print("[Arena] Opponent joined! Starting match.")
			_state = ArenaState.PLAYING
			_start_round()
		elif match_status in ["completed", "cancelled"]:
			print("[Arena] Match was %s while waiting." % match_status)
			if status_label:
				status_label.text = "Match %s." % match_status
			await get_tree().create_timer(2.0).timeout
			_show_lobby()
	elif result.status == 0:
		print("[Arena] Poll failed (offline), will retry...")


# ---------------------------------------------------------------------------
# Gameplay — rounds
# ---------------------------------------------------------------------------

func _start_round() -> void:
	var match_id: int = _current_match.get("id", 0)
	var current_round: int = _current_match.get("current_round", 1)
	var total_rounds: int = _current_match.get("total_rounds", 5)

	if round_label:
		round_label.text = "Round %d / %d" % [current_round, total_rounds]
		round_label.visible = true

	if status_label:
		status_label.text = "Loading challenge..."

	_set_visible(question_label, true)
	_set_visible(options_container, true)
	_set_visible(timer_label, true)
	_set_visible(score_label, true)
	_set_visible(match_type_buttons, false)
	_set_visible(result_container, false)

	print("[Arena] Fetching challenge for match #%d, round %d..." % [match_id, current_round])
	var result = await ApiClient.get("/arena/matches/%d/challenge/" % match_id)
	if result.status == 200 and result.data:
		_current_challenge = result.data
		_display_challenge(result.data)
		_round_start_time = Time.get_ticks_msec() / 1000.0
		_round_time_limit = float(result.data.get("time_limit_secs", 30))
		_round_timer_active = true
		if status_label:
			status_label.text = ""
	elif result.status == 0:
		if status_label:
			status_label.text = "Connection error — could not load challenge."
		print("[Arena] Failed to load challenge (offline)")
	else:
		if status_label:
			status_label.text = "Error loading challenge (status %d)." % result.status
		print("[Arena] Challenge request failed: status %d" % result.status)


func _display_challenge(data: Dictionary) -> void:
	var content: Dictionary = data.get("content", data)

	if question_label:
		var q_text = _localized(content, "question")
		if q_text == "":
			q_text = _localized(content, "prompt")
		if q_text == "":
			q_text = _localized(data, "question")
		question_label.text = q_text
		question_label.visible = true

	# Clear old option buttons
	if options_container:
		for child in options_container.get_children():
			child.queue_free()
	_option_buttons.clear()

	# Build new option buttons
	var options: Array = _localized_array(content, "options")
	if options.size() == 0:
		options = _localized_array(data, "options")

	if options_container:
		for i in range(options.size()):
			var btn := Button.new()
			btn.text = str(options[i])
			btn.toggle_mode = true
			btn.add_theme_font_size_override("font_size", 16)
			btn.custom_minimum_size.y = 44
			btn.pressed.connect(_on_answer_selected.bind(i))
			options_container.add_child(btn)
			_option_buttons.append(btn)

	# Update score display
	_update_score_display()


func _update_score_display() -> void:
	if not score_label:
		return
	var p1_score: int = _current_match.get("player1_score", 0)
	var p2_score: int = _current_match.get("player2_score", 0)
	var p1_name: String = _current_match.get("player1_name", "You")
	var p2_name: String = _current_match.get("player2_name", "Opponent")
	score_label.text = "%s: %d  |  %s: %d" % [p1_name, p1_score, p2_name, p2_score]


# ---------------------------------------------------------------------------
# Answer submission
# ---------------------------------------------------------------------------

func _on_answer_selected(answer_index: int) -> void:
	if _state != ArenaState.PLAYING:
		return

	_round_timer_active = false

	# Disable all option buttons to prevent double-submit
	for btn in _option_buttons:
		btn.disabled = true

	# Highlight selected button
	if answer_index >= 0 and answer_index < _option_buttons.size():
		_option_buttons[answer_index].button_pressed = true

	var elapsed = Time.get_ticks_msec() / 1000.0 - _round_start_time
	var time_taken = min(elapsed, _round_time_limit)

	var match_id: int = _current_match.get("id", 0)
	var current_round: int = _current_match.get("current_round", 1)
	var challenge_id = _current_challenge.get("id", _current_challenge.get("challenge_id", 0))

	print("[Arena] Submitting answer: match=%d round=%d challenge=%s answer=%d time=%.1fs" % [
		match_id, current_round, str(challenge_id), answer_index, time_taken,
	])

	if status_label:
		status_label.text = "Submitting..."

	var result = await ApiClient.post("/arena/submit/", {
		"match_id": match_id,
		"round_number": current_round,
		"challenge_id": challenge_id,
		"answer": answer_index,
		"time_taken_secs": time_taken,
	})

	if result.status in [200, 201] and result.data:
		_on_round_result(result.data)
	elif result.status == 0:
		if status_label:
			status_label.text = "Connection error — could not submit answer."
		print("[Arena] Submit failed (offline)")
	else:
		var detail = ""
		if result.data is Dictionary:
			detail = result.data.get("detail", result.data.get("error", ""))
		if status_label:
			status_label.text = "Submit error: %s" % detail if detail != "" else "Submit error (status %d)." % result.status
		print("[Arena] Submit failed: status %d — %s" % [result.status, detail])


# ---------------------------------------------------------------------------
# Round result
# ---------------------------------------------------------------------------

func _on_round_result(result: Dictionary) -> void:
	var is_correct: bool = result.get("is_correct", false)
	var correct_index: int = result.get("correct_answer", -1)

	# Highlight correct / wrong on buttons
	for i in range(_option_buttons.size()):
		if i == correct_index:
			_option_buttons[i].add_theme_color_override("font_color", Color(0.3, 1.0, 0.3))
		elif _option_buttons[i].button_pressed:
			_option_buttons[i].add_theme_color_override("font_color", Color(1.0, 0.3, 0.3))

	if status_label:
		if is_correct:
			status_label.text = "Correct!"
		else:
			status_label.text = "Wrong — the correct answer was highlighted."

	print("[Arena] Round result — correct: %s" % str(is_correct))

	# Update match data from result if provided
	if result.has("match"):
		_current_match = result.get("match", _current_match)
	# Also accept flat score fields
	if result.has("player1_score"):
		_current_match["player1_score"] = result.get("player1_score")
	if result.has("player2_score"):
		_current_match["player2_score"] = result.get("player2_score")

	_update_score_display()

	# Brief pause so the player can see feedback, then advance
	await get_tree().create_timer(2.0).timeout
	_check_match_state(result)


# ---------------------------------------------------------------------------
# Match state check — advance or finish
# ---------------------------------------------------------------------------

func _check_match_state(result_data: Dictionary) -> void:
	var match_status: String = ""

	# The result might carry the updated match, or we check _current_match
	if result_data.has("match") and result_data["match"] is Dictionary:
		match_status = result_data["match"].get("status", "")
		_current_match = result_data["match"]
	if match_status == "":
		match_status = _current_match.get("status", "")

	# If the match is now completed, show results
	if match_status == "completed":
		print("[Arena] Match completed!")
		_show_results(_current_match)
		return

	# Otherwise, refresh match state from server to get updated current_round
	var match_id: int = _current_match.get("id", 0)
	var refresh = await ApiClient.get("/arena/matches/%d/" % match_id)
	if refresh.status == 200 and refresh.data:
		_current_match = refresh.data
		match_status = refresh.data.get("status", "")

	if match_status == "completed":
		_show_results(_current_match)
	elif match_status == "in_progress":
		# Next round
		_start_round()
	else:
		# Unexpected state
		print("[Arena] Unexpected match status after round: %s" % match_status)
		if status_label:
			status_label.text = "Match in unexpected state: %s" % match_status
		await get_tree().create_timer(2.0).timeout
		_show_lobby()


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

func _show_results(match_data: Dictionary) -> void:
	_state = ArenaState.RESULTS
	_round_timer_active = false
	_current_match = match_data

	_set_visible(question_label, false)
	_set_visible(options_container, false)
	_set_visible(timer_label, false)
	_set_visible(round_label, false)
	_set_visible(match_type_buttons, false)
	_set_visible(realm_selector, false)
	_set_visible(result_container, true)
	_set_visible(score_label, true)
	_set_visible(back_button, true)

	var winner_id = match_data.get("winner_id", null)
	var p1_score: int = match_data.get("player1_score", 0)
	var p2_score: int = match_data.get("player2_score", 0)
	var p1_name: String = match_data.get("player1_name", "Player 1")
	var p2_name: String = match_data.get("player2_name", "Player 2")
	var elo_change: int = match_data.get("elo_change", 0)
	var is_draw: bool = match_data.get("is_draw", false)

	# Score display
	if score_label:
		score_label.text = "%s: %d  |  %s: %d" % [p1_name, p1_score, p2_name, p2_score]

	# Build result text
	var result_text := ""
	if is_draw:
		result_text = "It's a draw!"
	elif winner_id != null:
		var winner_name: String = match_data.get("winner_name", "")
		if winner_name == "":
			winner_name = "Winner"
		result_text = "%s wins!" % winner_name
	else:
		result_text = "Match over"

	if elo_change != 0:
		var sign = "+" if elo_change > 0 else ""
		result_text += "\nELO: %s%d" % [sign, elo_change]

	if status_label:
		status_label.text = result_text

	# Populate result container with detailed breakdown if available
	if result_container:
		for child in result_container.get_children():
			child.queue_free()

		var summary_label := RichTextLabel.new()
		summary_label.bbcode_enabled = true
		summary_label.fit_content = true
		summary_label.custom_minimum_size = Vector2(300, 0)

		var lines: PackedStringArray = []
		lines.append("[b]Match Results[/b]")
		lines.append("")
		lines.append("%s: [b]%d[/b]  vs  %s: [b]%d[/b]" % [p1_name, p1_score, p2_name, p2_score])

		if is_draw:
			lines.append("[color=#ffcc44]Draw![/color]")
		elif winner_id != null:
			lines.append("[color=#44ff88]%s wins![/color]" % match_data.get("winner_name", "Winner"))

		if elo_change != 0:
			var elo_color = "#44ff88" if elo_change > 0 else "#ff4444"
			var sign = "+" if elo_change > 0 else ""
			lines.append("[color=%s]ELO: %s%d[/color]" % [elo_color, sign, elo_change])

		summary_label.text = "\n".join(lines)
		result_container.add_child(summary_label)

		# Play Again button
		var play_again_btn := Button.new()
		play_again_btn.text = "Play Again"
		play_again_btn.add_theme_font_size_override("font_size", 18)
		play_again_btn.custom_minimum_size.y = 48
		play_again_btn.pressed.connect(_on_play_again)
		result_container.add_child(play_again_btn)

	print("[Arena] Results displayed — %s" % result_text.replace("\n", " | "))

	# Refresh stats so lobby shows updated ELO
	_load_stats()


func _on_play_again() -> void:
	# Clear realm selector children so they can be rebuilt
	if realm_selector:
		for child in realm_selector.get_children():
			child.queue_free()
	_show_lobby()


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

func _on_back_pressed() -> void:
	if _state == ArenaState.WAITING:
		# TODO: optionally cancel the match via API
		print("[Arena] Leaving while waiting for opponent")
	elif _state == ArenaState.PLAYING:
		print("[Arena] Leaving active match!")
	_state = ArenaState.LOBBY
	_round_timer_active = false
	SceneManager.goto_scene("world_hub")


# ---------------------------------------------------------------------------
# Timer display
# ---------------------------------------------------------------------------

func _update_timer(time_left: float) -> void:
	if timer_label:
		var seconds := int(ceil(time_left))
		timer_label.text = "%d" % seconds
		if time_left <= 5.0:
			timer_label.add_theme_color_override("font_color", Color(1.0, 0.3, 0.3))
		else:
			timer_label.remove_theme_color_override("font_color")


# ---------------------------------------------------------------------------
# Localization helpers
# ---------------------------------------------------------------------------

func _localized(data: Dictionary, base: String, fallback: String = "") -> String:
	## Bilingual field lookup using PlayerData.localized().
	return PlayerData.localized(data, base, fallback)


func _localized_array(data: Dictionary, base: String) -> Array:
	## Get localized array from data dict, falling back to English.
	var lang = PlayerData.preferred_lang if PlayerData.preferred_lang != "" else "en"
	var key = base + "_" + lang
	var value = data.get(key, [])
	if value == null or (value is Array and value.size() == 0):
		value = data.get(base + "_en", [])
	return value if value != null else []


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

func _set_visible(node: Control, visible: bool) -> void:
	if node:
		node.visible = visible
