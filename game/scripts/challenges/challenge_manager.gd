extends Node
## Manages challenge flow: loading, presenting, submitting, results.
## Uses ChallengeFactory to resolve display configuration per challenge type.

signal challenge_loaded(data: Dictionary)
signal answer_submitted()
signal result_received(result: Dictionary)
signal challenge_timer_tick(seconds_left: float)

var current_challenge: Dictionary = {}
var current_challenge_config: Dictionary = {}
var _time_started: float = 0.0
var _time_limit: float = 0.0
var _timer_active := false


func _process(_delta: float) -> void:
	if _timer_active and _time_limit > 0:
		var elapsed = Time.get_ticks_msec() / 1000.0 - _time_started
		var remaining = max(0, _time_limit - elapsed)
		challenge_timer_tick.emit(remaining)
		if remaining <= 0:
			_timer_active = false
			submit_answer({"timeout": true})


func load_challenge(challenge_id: int) -> void:
	var result = await ApiClient.get("/realms/challenges/%d/" % challenge_id)
	if result.status == 200 and result.data:
		current_challenge = result.data

		# Resolve display config via ChallengeFactory
		var challenge_type = result.data.get("challenge_type", "multiple_choice")
		current_challenge_config = ChallengeFactory.get_challenge_config(challenge_type)

		# Inject factory config and challenge_type into the emitted data so the
		# UI layer can use it without calling the factory again.
		result.data["_config"] = current_challenge_config
		if not result.data.has("challenge_type"):
			result.data["challenge_type"] = challenge_type

		_time_limit = result.data.get("time_limit_secs", 0)
		# For text-mode challenges with no time limit, skip the timer
		if _time_limit == null:
			_time_limit = 0
		_time_started = Time.get_ticks_msec() / 1000.0
		_timer_active = _time_limit > 0
		challenge_loaded.emit(result.data)


func get_config() -> Dictionary:
	## Returns the current challenge's display config from the factory.
	return current_challenge_config


func submit_answer(answer_data: Dictionary) -> void:
	_timer_active = false
	var elapsed = Time.get_ticks_msec() / 1000.0 - _time_started

	var payload = {
		"answer_data": answer_data,
		"time_taken_secs": elapsed,
	}

	answer_submitted.emit()

	var challenge_id = current_challenge.get("id", 0)
	var result = await ApiClient.post("/realms/challenges/%d/submit/" % challenge_id, payload)

	if result.status == 200 and result.data:
		result_received.emit(result.data)
		GameManager.complete_challenge(result.data)
	else:
		result_received.emit({"error": "Submission failed"})
