extends Node
## Manages challenge flow: loading, presenting, submitting, results.

signal challenge_loaded(data: Dictionary)
signal answer_submitted()
signal result_received(result: Dictionary)
signal challenge_timer_tick(seconds_left: float)

var current_challenge: Dictionary = {}
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
		_time_limit = result.data.get("time_limit_secs", 0)
		_time_started = Time.get_ticks_msec() / 1000.0
		_timer_active = _time_limit > 0
		challenge_loaded.emit(result.data)


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
