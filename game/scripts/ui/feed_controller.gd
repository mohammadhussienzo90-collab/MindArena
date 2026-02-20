extends Control
## Personalized feed UI — swipeable cards of tips, facts, challenges, quotes.

@onready var title_label: Label = $VBoxContainer/CardContainer/VBoxContainer/TitleLabel
@onready var body_label: RichTextLabel = $VBoxContainer/CardContainer/VBoxContainer/BodyLabel
@onready var type_label: Label = $VBoxContainer/CardContainer/VBoxContainer/TypeLabel
@onready var xp_label: Label = $VBoxContainer/CardContainer/VBoxContainer/XPLabel
@onready var like_button: Button = $VBoxContainer/HBoxContainer/LikeButton
@onready var complete_button: Button = $VBoxContainer/HBoxContainer/CompleteButton
@onready var next_button: Button = $VBoxContainer/HBoxContainer/NextButton
@onready var back_button: Button = $BackButton

var _feed_items: Array = []
var _current_index: int = 0


func _ready() -> void:
	like_button.pressed.connect(_on_like)
	complete_button.pressed.connect(_on_complete)
	next_button.pressed.connect(_on_next)
	back_button.pressed.connect(func(): SceneManager.goto_scene("world_hub"))
	_load_feed()


func _load_feed() -> void:
	var result = await ApiClient.get("/feed/")
	if result.status == 200 and result.data:
		_feed_items = result.data
		if _feed_items.size() > 0:
			_show_item(0)
		else:
			title_label.text = "No new content"
			body_label.text = "Check back later for fresh insights!"


func _show_item(index: int) -> void:
	if index >= _feed_items.size():
		title_label.text = "All caught up!"
		body_label.text = "You've seen all available content. Come back later."
		return

	_current_index = index
	var item = _feed_items[index]
	title_label.text = item.get("title_en", "")
	body_label.text = item.get("body_en", "")
	type_label.text = item.get("content_type", "").to_upper()
	xp_label.text = "+%d XP" % item.get("xp_value", 0)


func _on_like() -> void:
	if _current_index < _feed_items.size():
		var item_id = _feed_items[_current_index].get("id", 0)
		await ApiClient.post("/feed/%d/interact/" % item_id, {"liked": true})


func _on_complete() -> void:
	if _current_index < _feed_items.size():
		var item_id = _feed_items[_current_index].get("id", 0)
		await ApiClient.post("/feed/%d/interact/" % item_id, {"completed": true})
		_on_next()


func _on_next() -> void:
	_show_item(_current_index + 1)
