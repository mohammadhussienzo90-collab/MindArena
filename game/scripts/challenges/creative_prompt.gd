extends Control
## Free-text challenge UI controller.
## Used for creative_prompt and emotional_scenario challenge types where
## the player writes a response instead of selecting from options.

signal response_submitted(text: String)

@onready var prompt_label: RichTextLabel = $VBoxContainer/PromptLabel if has_node("VBoxContainer/PromptLabel") else null
@onready var text_input: TextEdit = $VBoxContainer/TextInput if has_node("VBoxContainer/TextInput") else null
@onready var char_count_label: Label = $VBoxContainer/CharCountLabel if has_node("VBoxContainer/CharCountLabel") else null
@onready var timer_bar: ProgressBar = $VBoxContainer/TimerBar if has_node("VBoxContainer/TimerBar") else null
@onready var submit_button: Button = $VBoxContainer/SubmitButton if has_node("VBoxContainer/SubmitButton") else null

var _challenge_data: Dictionary = {}
var _challenge_config: Dictionary = {}
var _min_text_length: int = 0


func _ready() -> void:
	if submit_button:
		submit_button.pressed.connect(_on_submit)
		submit_button.disabled = true
	if text_input:
		text_input.text_changed.connect(_on_text_changed)

	var cm = get_node_or_null("/root/ChallengeManager")
	if cm:
		cm.challenge_timer_tick.connect(_on_timer_tick)


func setup(challenge_data: Dictionary, config: Dictionary = {}) -> void:
	_challenge_data = challenge_data
	_challenge_config = config
	var content = challenge_data.get("content", {})

	# Determine the question/prompt key from factory config
	var question_key = config.get("question_key", "prompt")
	_min_text_length = config.get("min_text_length", 10)

	# Set prompt text (localized)
	if prompt_label:
		prompt_label.text = PlayerData.localized(content, question_key)

	# Timer setup
	var time_limit = challenge_data.get("time_limit_secs", 0)
	if timer_bar:
		var show_timer = config.get("show_timer", time_limit > 0)
		timer_bar.visible = show_timer and time_limit > 0
		timer_bar.max_value = time_limit if time_limit > 0 else 1
		timer_bar.value = time_limit if time_limit > 0 else 0

	# Reset input
	if text_input:
		text_input.text = ""
		text_input.placeholder_text = _get_placeholder()
		text_input.grab_focus()

	# Character count
	_update_char_count()

	# Submit starts disabled
	if submit_button:
		submit_button.disabled = true
		submit_button.text = PlayerData.localized(
			{"text_en": "Submit Response", "text_ar": "\u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0625\u062c\u0627\u0628\u0629"},
			"text", "Submit Response"
		)


func _get_placeholder() -> String:
	var lang = PlayerData.preferred_lang if PlayerData.preferred_lang != "" else "en"
	if lang == "ar":
		return "\u0627\u0643\u062a\u0628 \u0625\u062c\u0627\u0628\u062a\u0643 \u0647\u0646\u0627... (%d \u062d\u0631\u0641 \u0639\u0644\u0649 \u0627\u0644\u0623\u0642\u0644)" % _min_text_length
	return "Type your response here... (at least %d characters)" % _min_text_length


func _on_text_changed() -> void:
	_update_char_count()
	if submit_button and text_input:
		submit_button.disabled = text_input.text.strip_edges().length() < _min_text_length


func _update_char_count() -> void:
	if char_count_label and text_input:
		var count = text_input.text.strip_edges().length()
		if count < _min_text_length:
			char_count_label.text = "%d / %d" % [count, _min_text_length]
			char_count_label.add_theme_color_override("font_color", Color(0.8, 0.3, 0.3))
		else:
			char_count_label.text = "%d" % count
			char_count_label.add_theme_color_override("font_color", Color(0.3, 0.8, 0.3))


func _on_submit() -> void:
	if not text_input:
		return
	var response_text = text_input.text.strip_edges()
	if response_text.length() < _min_text_length:
		return

	# Disable further editing after submit
	text_input.editable = false
	if submit_button:
		submit_button.disabled = true

	response_submitted.emit(response_text)

	var cm = get_node_or_null("/root/ChallengeManager")
	if cm:
		cm.submit_answer({"text_response": response_text})


func _on_timer_tick(seconds_left: float) -> void:
	if timer_bar:
		timer_bar.value = seconds_left
