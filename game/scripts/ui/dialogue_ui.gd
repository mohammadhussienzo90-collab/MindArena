extends CanvasLayer
class_name DialogueUI
## Visual novel-style dialogue overlay.
## Shows speaker name, typewriter text, and choice buttons at the bottom of the screen.

const TYPEWRITER_SPEED := 0.03  # Seconds per character
const BG_COLOR := Color(0.0, 0.0, 0.0, 0.75)
const SPEAKER_COLOR := Color(0.3, 0.9, 0.95)
const TEXT_COLOR := Color(0.9, 0.9, 0.95)
const CHOICE_COLOR := Color(0.2, 0.7, 0.8)

var _panel: PanelContainer
var _speaker_label: Label
var _text_label: RichTextLabel
var _choices_container: VBoxContainer
var _skip_button: Button
var _continue_hint: Label

var _full_text: String = ""
var _visible_chars: int = 0
var _typing: bool = false
var _timer: Timer
var _current_options: Array = []


func _ready() -> void:
	layer = 90  # Above HUD but below transitions
	_build_ui()

	# Connect to DialogueManager if it exists as autoload
	var dm := _get_dialogue_manager()
	if dm:
		dm.dialogue_started.connect(_on_dialogue_started)
		dm.dialogue_line.connect(_on_dialogue_line)
		dm.dialogue_ended.connect(_on_dialogue_ended)


func _unhandled_input(event: InputEvent) -> void:
	if not _panel or not _panel.visible:
		return

	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_SPACE or event.keycode == KEY_ENTER:
			if _typing:
				_complete_text()
			elif _current_options.size() == 0:
				_advance()
			get_viewport().set_input_as_handled()

		if event.keycode == KEY_ESCAPE:
			_skip_all()
			get_viewport().set_input_as_handled()


func _build_ui() -> void:
	# Background dimmer
	var dimmer := ColorRect.new()
	dimmer.color = Color(0, 0, 0, 0.3)
	dimmer.anchors_preset = Control.PRESET_FULL_RECT
	dimmer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dimmer)

	# Dialogue panel at bottom
	_panel = PanelContainer.new()
	_panel.name = "DialoguePanel"
	_panel.anchor_left = 0.05
	_panel.anchor_right = 0.95
	_panel.anchor_top = 0.7
	_panel.anchor_bottom = 0.95
	_panel.offset_left = 0
	_panel.offset_right = 0
	_panel.offset_top = 0
	_panel.offset_bottom = 0

	var style := StyleBoxFlat.new()
	style.bg_color = BG_COLOR
	style.corner_radius_top_left = 12
	style.corner_radius_top_right = 12
	style.corner_radius_bottom_left = 12
	style.corner_radius_bottom_right = 12
	style.content_margin_left = 24
	style.content_margin_right = 24
	style.content_margin_top = 16
	style.content_margin_bottom = 16
	_panel.add_theme_stylebox_override("panel", style)
	add_child(_panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	_panel.add_child(vbox)

	# Speaker name
	_speaker_label = Label.new()
	_speaker_label.add_theme_font_size_override("font_size", 22)
	_speaker_label.add_theme_color_override("font_color", SPEAKER_COLOR)
	vbox.add_child(_speaker_label)

	# Dialogue text with typewriter
	_text_label = RichTextLabel.new()
	_text_label.bbcode_enabled = true
	_text_label.fit_content = true
	_text_label.custom_minimum_size = Vector2(0, 60)
	_text_label.add_theme_font_size_override("normal_font_size", 18)
	_text_label.add_theme_color_override("default_color", TEXT_COLOR)
	_text_label.scroll_active = false
	vbox.add_child(_text_label)

	# Choices container
	_choices_container = VBoxContainer.new()
	_choices_container.add_theme_constant_override("separation", 6)
	vbox.add_child(_choices_container)

	# Continue hint
	_continue_hint = Label.new()
	_continue_hint.text = "Press SPACE to continue..."
	_continue_hint.add_theme_font_size_override("font_size", 14)
	_continue_hint.add_theme_color_override("font_color", Color(0.6, 0.6, 0.7, 0.6))
	_continue_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	vbox.add_child(_continue_hint)

	# Skip button (top-right)
	_skip_button = Button.new()
	_skip_button.text = "Skip >"
	_skip_button.flat = true
	_skip_button.anchor_left = 0.9
	_skip_button.anchor_right = 0.98
	_skip_button.anchor_top = 0.67
	_skip_button.anchor_bottom = 0.72
	_skip_button.add_theme_color_override("font_color", Color(0.5, 0.5, 0.6))
	_skip_button.pressed.connect(_skip_all)
	add_child(_skip_button)

	# Typewriter timer
	_timer = Timer.new()
	_timer.wait_time = TYPEWRITER_SPEED
	_timer.timeout.connect(_on_typewriter_tick)
	add_child(_timer)

	# Start hidden
	_panel.visible = false
	_skip_button.visible = false


func _on_dialogue_started(_id: String) -> void:
	_panel.visible = true
	_skip_button.visible = true
	# Capture mouse for dialogue
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _on_dialogue_line(speaker: String, text: String, options: Array) -> void:
	_speaker_label.text = speaker
	_full_text = text
	_visible_chars = 0
	_text_label.text = ""
	_current_options = options
	_typing = true

	# Clear old choices
	for child in _choices_container.get_children():
		child.queue_free()

	_continue_hint.visible = false
	_timer.start()


func _on_dialogue_ended(_id: String) -> void:
	_panel.visible = false
	_skip_button.visible = false
	_timer.stop()
	_typing = false


func _on_typewriter_tick() -> void:
	if _visible_chars < _full_text.length():
		_visible_chars += 1
		_text_label.text = _full_text.substr(0, _visible_chars)
	else:
		_timer.stop()
		_typing = false
		_text_label.text = _full_text
		_show_options_or_continue()


func _complete_text() -> void:
	_timer.stop()
	_typing = false
	_visible_chars = _full_text.length()
	_text_label.text = _full_text
	_show_options_or_continue()


func _show_options_or_continue() -> void:
	if _current_options.size() > 0:
		_continue_hint.visible = false
		for i in range(_current_options.size()):
			var option: Dictionary = _current_options[i]
			var btn := Button.new()
			var lang := PlayerData.preferred_lang if PlayerData.preferred_lang != "" else "en"
			btn.text = option.get("text_" + lang, option.get("text_en", option.get("text", "...")))
			btn.add_theme_font_size_override("font_size", 16)
			btn.add_theme_color_override("font_color", CHOICE_COLOR)
			var idx := i
			btn.pressed.connect(func(): _on_choice_selected(idx))
			_choices_container.add_child(btn)
	else:
		_continue_hint.visible = true


func _on_choice_selected(index: int) -> void:
	_current_options = []
	var dm := _get_dialogue_manager()
	if dm:
		dm.advance(index)


func _advance() -> void:
	var dm := _get_dialogue_manager()
	if dm:
		dm.advance()


func _skip_all() -> void:
	var dm := _get_dialogue_manager()
	if dm:
		dm.skip()


func _get_dialogue_manager() -> Node:
	# Look for DialogueManager as autoload or in scene tree
	if has_node("/root/DialogueManager"):
		return get_node("/root/DialogueManager")
	# Try parent scene
	var scene := get_tree().current_scene
	if scene:
		var dm := scene.find_child("DialogueManager", true, false)
		if dm:
			return dm
	return null
