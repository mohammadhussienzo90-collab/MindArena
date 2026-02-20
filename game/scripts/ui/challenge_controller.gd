extends Control
## Challenge screen UI controller.
## Connects UI elements to the ChallengeManager logic node.
## Uses ChallengeFactory config (injected via data["_config"]) to drive
## presentation without hard-coding every challenge type.

@onready var title_label: Label = $VBoxContainer/HeaderHBox/TitleLabel
@onready var timer_bar: ProgressBar = $VBoxContainer/HeaderHBox/TimerBar
@onready var difficulty_label: Label = $VBoxContainer/DifficultyLabel
@onready var question_label: RichTextLabel = $VBoxContainer/QuestionLabel
@onready var options_container: VBoxContainer = $VBoxContainer/OptionsContainer
@onready var xp_label: Label = $VBoxContainer/XPLabel
@onready var explanation_panel: PanelContainer = $VBoxContainer/ExplanationPanel
@onready var explanation_label: RichTextLabel = $VBoxContainer/ExplanationPanel/ExplanationLabel
@onready var next_button: Button = $VBoxContainer/NextButton

var _challenge_manager: Node
var _option_buttons: Array[Button] = []
var _selected_index: int = -1
var _challenge_queue: Array = []
var _current_queue_index: int = 0
var _current_config: Dictionary = {}


func _ready() -> void:
	# ChallengeManager is a child node or we create one
	_challenge_manager = Node.new()
	_challenge_manager.set_script(load("res://scripts/challenges/challenge_manager.gd"))
	_challenge_manager.name = "ChallengeManager"
	add_child(_challenge_manager)

	_challenge_manager.challenge_loaded.connect(_on_challenge_loaded)
	_challenge_manager.result_received.connect(_on_result_received)
	_challenge_manager.challenge_timer_tick.connect(_on_timer_tick)

	next_button.pressed.connect(_on_next)
	next_button.visible = false
	explanation_panel.visible = false

	# Load the challenge — realm slug passed via GameManager
	_load_realm_challenges()


func _load_realm_challenges() -> void:
	var realm = GameManager.current_realm
	if realm.is_empty():
		title_label.text = "No realm selected"
		return

	title_label.text = "Loading..."
	question_label.text = "Preparing challenges..."

	var result = await ApiClient.get("/realms/%s/challenges/" % realm)
	if result.status == 200 and result.data:
		_challenge_queue = result.data
		if _challenge_queue.size() > 0:
			_current_queue_index = 0
			_challenge_manager.load_challenge(_challenge_queue[0].get("id", 0))
		else:
			title_label.text = "Empty Realm"
			question_label.text = "No challenges available in this realm yet."
	elif result.status == 0:
		title_label.text = "Connection Error"
		question_label.text = "Server unreachable. Please check your connection and try again."
	else:
		title_label.text = "Error"
		question_label.text = "Could not load challenges (Error %d)." % result.get("status", 0)


func _lang_key(base: String) -> String:
	## Return language-suffixed key (e.g. "question_ar" or "question_en").
	var lang = PlayerData.preferred_lang if PlayerData.preferred_lang != "" else "en"
	return base + "_" + lang


func _localized_content(content: Dictionary, base: String, fallback: String = "") -> String:
	## Get localized text from content dict, falling back to English.
	var value = content.get(_lang_key(base), "")
	if value == "" or value == null:
		value = content.get(base + "_en", fallback)
	return value if value != null else fallback


func _localized_array(content: Dictionary, base: String) -> Array:
	## Get localized array from content dict, falling back to English.
	var value = content.get(_lang_key(base), [])
	if value == null or (value is Array and value.size() == 0):
		value = content.get(base + "_en", [])
	return value if value != null else []


func _localized_choice_text(choice, _index: int) -> String:
	## Extract display text from a choice item.
	## Choices may be plain strings or dicts with text_en/text_ar keys.
	if choice is Dictionary:
		return _localized_content(choice, "text", "Option %d" % (_index + 1))
	return str(choice)


func _on_challenge_loaded(data: Dictionary) -> void:
	var content = data.get("content", {})
	var challenge_type = data.get("challenge_type", "multiple_choice")

	# Get factory config — ChallengeManager injects it as _config
	_current_config = data.get("_config", ChallengeFactory.get_challenge_config(challenge_type))
	var input_mode: String = _current_config.get("input_mode", "options")
	var question_key: String = _current_config.get("question_key", "question")
	var options_key: String = _current_config.get("options_key", "options")
	var auto_submit: bool = _current_config.get("auto_submit", false)
	var timer_prominent: bool = _current_config.get("timer_prominent", false)

	title_label.text = PlayerData.localized(data, "title", "Challenge")
	difficulty_label.text = "Difficulty: %d / 10" % data.get("difficulty", 1)
	xp_label.text = "+%d XP" % data.get("base_xp", 10)

	# Timer — use factory config to decide visibility and style
	var time_limit = data.get("time_limit_secs", 0)
	if time_limit == null:
		time_limit = 0
	var show_timer: bool = _current_config.get("show_timer", true) and time_limit > 0
	timer_bar.visible = show_timer
	timer_bar.max_value = time_limit if time_limit > 0 else 1
	timer_bar.value = time_limit if time_limit > 0 else 0

	# Visual emphasis for timed_response / math_logic
	if timer_prominent and show_timer:
		timer_bar.custom_minimum_size.y = 24
		timer_bar.add_theme_color_override("font_color", Color(1, 0.85, 0.2))
	else:
		timer_bar.custom_minimum_size.y = 12
		timer_bar.remove_theme_color_override("font_color")

	# Hide result UI
	explanation_panel.visible = false
	next_button.visible = false
	_selected_index = -1

	# Clear old options / input widgets
	for child in options_container.get_children():
		child.queue_free()
	_option_buttons.clear()

	# ── Build UI based on input_mode from factory ────────────────────
	match input_mode:
		"options":
			# Standard MCQ: pattern_match, sequence, math_logic, timed_response, multiple_choice
			question_label.text = _localized_content(content, question_key)
			var options = _localized_array(content, options_key)
			_build_option_buttons(options, auto_submit)

		"choices":
			# Scenario-based with richer choice objects (scenario_choice, financial_decision)
			question_label.text = _localized_content(content, question_key)
			var choices = _localized_array(content, options_key)
			var choice_texts: Array[String] = []
			for i in range(choices.size()):
				choice_texts.append(_localized_choice_text(choices[i], i))
			_build_option_buttons(choice_texts, auto_submit)

		"text":
			# Free-text input (creative_prompt, emotional_scenario)
			question_label.text = _localized_content(content, question_key)
			_build_text_input()

		_:
			# Ultimate fallback — try options, then text
			question_label.text = _localized_content(content, question_key, _localized_content(content, "question", "Challenge"))
			var options = _localized_array(content, options_key)
			if options.size() > 0:
				_build_option_buttons(options, auto_submit)
			else:
				_build_text_input()


func _build_option_buttons(items: Array, auto_submit: bool = false) -> void:
	## Create toggle buttons for each selectable option.
	for i in range(items.size()):
		var btn = Button.new()
		btn.text = str(items[i])
		btn.toggle_mode = true
		if auto_submit:
			btn.pressed.connect(_on_option_auto_submit.bind(i))
		else:
			btn.pressed.connect(_on_option_pressed.bind(i))
		btn.add_theme_font_size_override("font_size", 16)
		options_container.add_child(btn)
		_option_buttons.append(btn)

	# For non-auto-submit modes, add a confirm button
	if not auto_submit and items.size() > 0:
		var confirm_btn = Button.new()
		confirm_btn.name = "ConfirmBtn"
		confirm_btn.text = PlayerData.localized(
			{"text_en": "Confirm", "text_ar": "\u062a\u0623\u0643\u064a\u062f"},
			"text", "Confirm"
		)
		confirm_btn.disabled = true
		confirm_btn.add_theme_font_size_override("font_size", 16)
		confirm_btn.add_theme_color_override("font_color", Color(0.2, 0.9, 0.4))
		options_container.add_child(confirm_btn)
		confirm_btn.pressed.connect(func():
			if _selected_index >= 0:
				confirm_btn.disabled = true
				_challenge_manager.submit_answer({"selected_index": _selected_index})
		)


func _build_text_input() -> void:
	## Create a multi-line TextEdit + Submit button for free-text challenges.
	var min_len: int = _current_config.get("min_text_length", 10)

	var text_edit = TextEdit.new()
	text_edit.name = "ResponseInput"
	text_edit.placeholder_text = _get_text_placeholder(min_len)
	text_edit.custom_minimum_size = Vector2(0, 120)
	text_edit.size_flags_vertical = Control.SIZE_EXPAND_FILL
	text_edit.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	options_container.add_child(text_edit)

	var char_label = Label.new()
	char_label.name = "CharCount"
	char_label.text = "0 / %d" % min_len
	char_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	char_label.add_theme_color_override("font_color", Color(0.8, 0.3, 0.3))
	options_container.add_child(char_label)

	var submit_btn = Button.new()
	submit_btn.name = "TextSubmitBtn"
	submit_btn.text = PlayerData.localized(
		{"text_en": "Submit Response", "text_ar": "\u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0625\u062c\u0627\u0628\u0629"},
		"text", "Submit Response"
	)
	submit_btn.disabled = true
	submit_btn.add_theme_font_size_override("font_size", 16)
	options_container.add_child(submit_btn)

	# Wire up character counting and validation
	text_edit.text_changed.connect(func():
		var count = text_edit.text.strip_edges().length()
		if count < min_len:
			char_label.text = "%d / %d" % [count, min_len]
			char_label.add_theme_color_override("font_color", Color(0.8, 0.3, 0.3))
			submit_btn.disabled = true
		else:
			char_label.text = "%d" % count
			char_label.add_theme_color_override("font_color", Color(0.3, 0.8, 0.3))
			submit_btn.disabled = false
	)

	submit_btn.pressed.connect(func():
		var response_text = text_edit.text.strip_edges()
		if response_text.length() >= min_len:
			text_edit.editable = false
			submit_btn.disabled = true
			_challenge_manager.submit_answer({"text_response": response_text})
	)

	text_edit.grab_focus()


func _get_text_placeholder(min_len: int) -> String:
	var lang = PlayerData.preferred_lang if PlayerData.preferred_lang != "" else "en"
	if lang == "ar":
		return "\u0627\u0643\u062a\u0628 \u0625\u062c\u0627\u0628\u062a\u0643 \u0647\u0646\u0627... (%d \u062d\u0631\u0641 \u0639\u0644\u0649 \u0627\u0644\u0623\u0642\u0644)" % min_len
	return "Type your response here... (at least %d characters)" % min_len


func _on_option_pressed(index: int) -> void:
	_selected_index = index
	for i in range(_option_buttons.size()):
		_option_buttons[i].button_pressed = (i == index)
	# Enable the confirm button if present
	var confirm_btn = options_container.get_node_or_null("ConfirmBtn")
	if confirm_btn:
		confirm_btn.disabled = false


func _on_option_auto_submit(index: int) -> void:
	## For timed_response and similar: select and immediately submit.
	_selected_index = index
	for i in range(_option_buttons.size()):
		_option_buttons[i].button_pressed = (i == index)
	_challenge_manager.submit_answer({"selected_index": index})


func _on_result_received(result: Dictionary) -> void:
	if result.has("error"):
		explanation_label.text = result.get("error", "Something went wrong.")
	else:
		var correct = result.get("is_correct", false)
		var xp = result.get("base_xp", 0) + result.get("bonus_xp", 0)
		var explanation = _localized_content(result, "explanation", result.get("explanation", ""))

		# Highlight correct/wrong
		if _selected_index >= 0 and _selected_index < _option_buttons.size():
			var btn = _option_buttons[_selected_index]
			if correct:
				btn.add_theme_color_override("font_color", Color(0.3, 1, 0.3))
			else:
				btn.add_theme_color_override("font_color", Color(1, 0.3, 0.3))

		xp_label.text = "+%d XP %s" % [xp, "Correct!" if correct else ""]
		explanation_label.text = explanation

	explanation_panel.visible = true
	next_button.visible = true

	# Disable option buttons and confirm button
	for btn in _option_buttons:
		btn.disabled = true
	var confirm_btn = options_container.get_node_or_null("ConfirmBtn")
	if confirm_btn:
		confirm_btn.disabled = true


func _on_timer_tick(seconds_left: float) -> void:
	timer_bar.value = seconds_left


func _on_next() -> void:
	_current_queue_index += 1
	if _current_queue_index < _challenge_queue.size():
		_challenge_manager.load_challenge(_challenge_queue[_current_queue_index].get("id", 0))
	else:
		# All challenges done — refresh stats so world reflects progress
		await PlayerData.load_realm_stats()
		SceneManager.goto_scene("world_hub")
