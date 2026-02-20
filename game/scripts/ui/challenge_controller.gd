extends Control
## Challenge screen UI controller.
## Connects UI elements to the ChallengeManager logic node.

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

	var result = await ApiClient.get("/realms/%s/challenges/" % realm)
	if result.status == 200 and result.data:
		_challenge_queue = result.data
		if _challenge_queue.size() > 0:
			_current_queue_index = 0
			_challenge_manager.load_challenge(_challenge_queue[0].get("id", 0))
		else:
			question_label.text = "No challenges available in this realm yet."
	else:
		question_label.text = "Could not load challenges. Check your connection."


func _on_challenge_loaded(data: Dictionary) -> void:
	var content = data.get("content", {})
	var challenge_type = data.get("challenge_type", "multiple_choice")

	title_label.text = data.get("title_en", "Challenge")
	difficulty_label.text = "Difficulty: %d / 10" % data.get("difficulty", 1)
	xp_label.text = "+%d XP" % data.get("base_xp", 10)

	# Timer
	var time_limit = data.get("time_limit_secs", 0)
	timer_bar.visible = time_limit > 0
	timer_bar.max_value = time_limit
	timer_bar.value = time_limit

	# Hide result UI
	explanation_panel.visible = false
	next_button.visible = false
	_selected_index = -1

	# Clear old options
	for child in options_container.get_children():
		child.queue_free()
	_option_buttons.clear()

	if challenge_type == "multiple_choice":
		question_label.text = content.get("question_en", "")
		var options = content.get("options_en", [])
		for i in range(options.size()):
			var btn = Button.new()
			btn.text = options[i]
			btn.toggle_mode = true
			btn.pressed.connect(_on_option_pressed.bind(i))
			btn.add_theme_font_size_override("font_size", 16)
			options_container.add_child(btn)
			_option_buttons.append(btn)

	elif challenge_type == "scenario_choice":
		question_label.text = content.get("scenario_en", "")
		var choices = content.get("choices_en", [])
		for i in range(choices.size()):
			var btn = Button.new()
			btn.text = choices[i]
			btn.toggle_mode = true
			btn.pressed.connect(_on_option_pressed.bind(i))
			btn.add_theme_font_size_override("font_size", 16)
			options_container.add_child(btn)
			_option_buttons.append(btn)

	elif challenge_type == "creative_prompt":
		question_label.text = content.get("prompt_en", "")
		var input = LineEdit.new()
		input.placeholder_text = "Type your response..."
		input.custom_minimum_size.y = 40
		options_container.add_child(input)
		var submit_btn = Button.new()
		submit_btn.text = "Submit Response"
		submit_btn.pressed.connect(func():
			_challenge_manager.submit_answer({"text_response": input.text})
		)
		options_container.add_child(submit_btn)

	else:
		# Fallback for pattern_match, sequence, math_logic, timed_response, etc.
		# Render as multiple choice if options exist, otherwise as text prompt
		var options = content.get("options_en", [])
		if options.size() > 0:
			question_label.text = content.get("question_en", content.get("prompt_en", ""))
			for i in range(options.size()):
				var btn = Button.new()
				btn.text = options[i]
				btn.toggle_mode = true
				btn.pressed.connect(_on_option_pressed.bind(i))
				btn.add_theme_font_size_override("font_size", 16)
				options_container.add_child(btn)
				_option_buttons.append(btn)
		else:
			question_label.text = content.get("question_en", content.get("prompt_en", "Challenge"))
			var input = LineEdit.new()
			input.placeholder_text = "Enter your answer..."
			input.custom_minimum_size.y = 40
			options_container.add_child(input)
			var submit_btn = Button.new()
			submit_btn.text = "Submit"
			submit_btn.pressed.connect(func():
				_challenge_manager.submit_answer({"text_response": input.text})
			)
			options_container.add_child(submit_btn)


func _on_option_pressed(index: int) -> void:
	_selected_index = index
	for i in range(_option_buttons.size()):
		_option_buttons[i].button_pressed = (i == index)
	# Auto-submit on selection
	_challenge_manager.submit_answer({"selected_index": index})


func _on_result_received(result: Dictionary) -> void:
	if result.has("error"):
		explanation_label.text = result.get("error", "Something went wrong.")
	else:
		var correct = result.get("is_correct", false)
		var xp = result.get("base_xp", 0) + result.get("bonus_xp", 0)
		var explanation = result.get("explanation", "")

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

	# Disable option buttons
	for btn in _option_buttons:
		btn.disabled = true


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
