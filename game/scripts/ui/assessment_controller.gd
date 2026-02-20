extends Control
## Personality assessment UI — onboarding flow.

signal assessment_completed(result: Dictionary)

@onready var question_label: RichTextLabel = $VBoxContainer/QuestionLabel
@onready var options_container: VBoxContainer = $VBoxContainer/OptionsContainer
@onready var progress_bar: ProgressBar = $VBoxContainer/ProgressBar
@onready var progress_label: Label = $VBoxContainer/ProgressLabel

var _questions: Array = []
var _current_index: int = 0
var _answers: Array[int] = []
var _option_labels := ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]


func _ready() -> void:
	_load_questions()


func _load_questions() -> void:
	var result = await ApiClient.get("/assessment/questions/")
	if result.status == 200 and result.data:
		_questions = result.data.get("questions", [])
		if _questions.size() > 0:
			_show_question(0)
		else:
			push_error("[Assessment] No questions loaded")


func _show_question(index: int) -> void:
	if index >= _questions.size():
		_submit_assessment()
		return

	_current_index = index
	var q = _questions[index]
	question_label.text = q.get("text", "")
	progress_bar.max_value = _questions.size()
	progress_bar.value = index
	progress_label.text = "%d / %d" % [index + 1, _questions.size()]

	# Clear old options
	for child in options_container.get_children():
		child.queue_free()

	# Create 1-5 scale buttons
	for i in range(5):
		var btn = Button.new()
		btn.text = _option_labels[i]
		btn.pressed.connect(_on_answer.bind(i + 1))
		btn.add_theme_font_size_override("font_size", 16)
		options_container.add_child(btn)


func _on_answer(value: int) -> void:
	_answers.append(value)
	_show_question(_current_index + 1)


func _submit_assessment() -> void:
	question_label.text = "Analyzing your personality..."
	for child in options_container.get_children():
		child.queue_free()

	var result = await ApiClient.post("/assessment/submit/", {"answers": _answers})
	if result.status == 200 and result.data:
		# Store Big Five personality trait scores in PlayerData
		var traits := {}
		for trait_key in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
			if result.data.has(trait_key):
				traits[trait_key] = result.data[trait_key]
		if traits.size() > 0:
			PlayerData.personality_traits = traits
			PlayerData.data_updated.emit()

		assessment_completed.emit(result.data)
		PlayerData.onboarding_done = true
		question_label.text = "Assessment complete! Your mind world is taking shape..."
		await get_tree().create_timer(2.0).timeout
		SceneManager.goto_scene("world_hub")
	else:
		question_label.text = "Something went wrong. Please try again."
