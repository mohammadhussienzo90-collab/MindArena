extends Control
## Multiple choice question challenge UI.

signal answer_selected(index: int)

@onready var question_label: RichTextLabel = $VBoxContainer/QuestionLabel
@onready var options_container: VBoxContainer = $VBoxContainer/OptionsContainer
@onready var timer_bar: ProgressBar = $VBoxContainer/TimerBar
@onready var submit_button: Button = $VBoxContainer/SubmitButton

var _selected_index: int = -1
var _challenge_data: Dictionary = {}
var _option_buttons: Array[Button] = []


func _ready() -> void:
	submit_button.pressed.connect(_on_submit)
	submit_button.disabled = true

	var cm = get_node_or_null("/root/ChallengeManager")
	if cm:
		cm.challenge_timer_tick.connect(_on_timer_tick)


func setup(challenge_data: Dictionary) -> void:
	_challenge_data = challenge_data
	var content = challenge_data.get("content", {})

	question_label.text = content.get("question_en", "")

	# Clear old options
	for child in options_container.get_children():
		child.queue_free()
	_option_buttons.clear()

	# Create option buttons
	var options = content.get("options_en", [])
	for i in range(options.size()):
		var btn = Button.new()
		btn.text = options[i]
		btn.toggle_mode = true
		btn.pressed.connect(_on_option_pressed.bind(i))
		btn.add_theme_font_size_override("font_size", 18)
		options_container.add_child(btn)
		_option_buttons.append(btn)

	# Timer
	var time_limit = challenge_data.get("time_limit_secs", 0)
	timer_bar.visible = time_limit > 0
	timer_bar.max_value = time_limit
	timer_bar.value = time_limit


func _on_option_pressed(index: int) -> void:
	_selected_index = index
	submit_button.disabled = false
	for i in range(_option_buttons.size()):
		_option_buttons[i].button_pressed = (i == index)
	answer_selected.emit(index)


func _on_submit() -> void:
	if _selected_index >= 0:
		var cm = get_node_or_null("/root/ChallengeManager")
		if cm:
			cm.submit_answer({"selected_index": _selected_index})


func _on_timer_tick(seconds_left: float) -> void:
	timer_bar.value = seconds_left
