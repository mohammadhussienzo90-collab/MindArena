extends Control
## AI Companion chat UI controller.

@onready var messages_container: VBoxContainer = $Panel/VBoxContainer/ScrollContainer/MessagesContainer
@onready var input_field: LineEdit = $Panel/VBoxContainer/HBoxContainer/InputField
@onready var send_button: Button = $Panel/VBoxContainer/HBoxContainer/SendButton
@onready var scroll_container: ScrollContainer = $Panel/VBoxContainer/ScrollContainer

var _conversation_id: int = -1
var _waiting_for_reply := false


func _ready() -> void:
	send_button.pressed.connect(_on_send)
	input_field.text_submitted.connect(_on_text_submitted)


func _on_send() -> void:
	_send_message()


func _on_text_submitted(_text: String) -> void:
	_send_message()


func _send_message() -> void:
	var text = input_field.text.strip_edges()
	if text.is_empty() or _waiting_for_reply:
		return

	_add_message_bubble(text, true)
	input_field.text = ""
	_waiting_for_reply = true

	var payload = {"message": text}
	if _conversation_id > 0:
		payload["conversation_id"] = _conversation_id

	var result = await ApiClient.post("/companion/chat/", payload)

	_waiting_for_reply = false
	if result.status == 200 and result.data:
		_conversation_id = result.data.get("conversation_id", -1)
		_add_message_bubble(result.data.get("reply", "..."), false)
	else:
		_add_message_bubble("(Connection error. Try again.)", false)


func _add_message_bubble(text: String, is_player: bool) -> void:
	var label = RichTextLabel.new()
	label.bbcode_enabled = true
	label.fit_content = true
	label.custom_minimum_size.x = 300

	if is_player:
		label.text = "[right][color=#4488ff]%s[/color][/right]" % text
	else:
		label.text = "[color=#44ff88]Noor:[/color] %s" % text

	messages_container.add_child(label)

	# Auto-scroll to bottom
	await get_tree().process_frame
	scroll_container.scroll_vertical = scroll_container.get_v_scroll_bar().max_value
