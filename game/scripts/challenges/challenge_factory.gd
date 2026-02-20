class_name ChallengeFactory
extends RefCounted
## Factory that returns display configuration for each challenge type.
##
## All MindArena challenge types ultimately fall into one of three input modes:
##   "options"  – player picks from a list of choices (MCQ, pattern, math, etc.)
##   "choices"  – player picks from scenario-style choices with richer text
##   "text"     – player writes a free-text response
##
## The returned Dictionary tells the UI *how* to present the challenge without
## the UI needing to hard-code knowledge about every challenge_type string.


## ── Public API ──────────────────────────────────────────────────────────────

static func get_challenge_config(challenge_type: String) -> Dictionary:
	## Returns a config dictionary describing how the challenge should be displayed.
	##
	## Keys:
	##   input_mode       : "options" | "choices" | "text"
	##   show_timer       : bool – whether to show the timer bar at all
	##   timer_prominent  : bool – whether the timer should be visually emphasised
	##   show_scenario    : bool – whether to show longer scenario/prompt text
	##   question_key     : String – the base field name for the main text
	##   options_key      : String – the base field name for the selectable items
	##   auto_submit      : bool – submit immediately on option select (speed rounds)
	##   min_text_length  : int  – minimum characters for free-text answers (0 = none)

	match challenge_type:
		# ── Standard option-based types ──────────────────────────────
		"multiple_choice":
			return {
				"input_mode": "options",
				"show_timer": true,
				"timer_prominent": false,
				"show_scenario": false,
				"question_key": "question",
				"options_key": "options",
				"auto_submit": false,
				"min_text_length": 0,
			}

		"pattern_match":
			return {
				"input_mode": "options",
				"show_timer": true,
				"timer_prominent": false,
				"show_scenario": false,
				"question_key": "question",
				"options_key": "options",
				"auto_submit": false,
				"min_text_length": 0,
			}

		"sequence":
			return {
				"input_mode": "options",
				"show_timer": true,
				"timer_prominent": false,
				"show_scenario": false,
				"question_key": "question",
				"options_key": "options",
				"auto_submit": false,
				"min_text_length": 0,
			}

		"math_logic":
			return {
				"input_mode": "options",
				"show_timer": true,
				"timer_prominent": true,
				"show_scenario": false,
				"question_key": "question",
				"options_key": "options",
				"auto_submit": false,
				"min_text_length": 0,
			}

		"timed_response":
			return {
				"input_mode": "options",
				"show_timer": true,
				"timer_prominent": true,
				"show_scenario": false,
				"question_key": "question",
				"options_key": "options",
				"auto_submit": true,
				"min_text_length": 0,
			}

		# ── Scenario / longer-text types with selectable choices ─────
		"scenario_choice":
			return {
				"input_mode": "choices",
				"show_timer": true,
				"timer_prominent": false,
				"show_scenario": true,
				"question_key": "scenario",
				"options_key": "choices",
				"auto_submit": false,
				"min_text_length": 0,
			}

		"emotional_scenario":
			return {
				"input_mode": "text",
				"show_timer": false,
				"timer_prominent": false,
				"show_scenario": true,
				"question_key": "prompt",
				"options_key": "",
				"auto_submit": false,
				"min_text_length": 10,
			}

		"financial_decision":
			return {
				"input_mode": "choices",
				"show_timer": true,
				"timer_prominent": false,
				"show_scenario": true,
				"question_key": "scenario",
				"options_key": "choices",
				"auto_submit": false,
				"min_text_length": 0,
			}

		# ── Free-text types ──────────────────────────────────────────
		"creative_prompt":
			return {
				"input_mode": "text",
				"show_timer": true,
				"timer_prominent": false,
				"show_scenario": true,
				"question_key": "prompt",
				"options_key": "",
				"auto_submit": false,
				"min_text_length": 20,
			}

		# ── Unknown / fallback ───────────────────────────────────────
		_:
			return _fallback_config()


static func is_options_type(challenge_type: String) -> bool:
	## Returns true if the challenge type uses selectable options/choices.
	var config = get_challenge_config(challenge_type)
	return config.input_mode in ["options", "choices"]


static func is_text_type(challenge_type: String) -> bool:
	## Returns true if the challenge type requires free-text input.
	var config = get_challenge_config(challenge_type)
	return config.input_mode == "text"


## ── Private helpers ─────────────────────────────────────────────────────────

static func _fallback_config() -> Dictionary:
	## Sensible default: treat unknown types as option-based MCQ.
	return {
		"input_mode": "options",
		"show_timer": true,
		"timer_prominent": false,
		"show_scenario": false,
		"question_key": "question",
		"options_key": "options",
		"auto_submit": false,
		"min_text_length": 0,
	}
