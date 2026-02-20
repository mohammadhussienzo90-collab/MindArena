extends CanvasLayer
## In-game HUD: XP bar, level, realm info, streak, nav buttons, notifications.

@onready var level_label: Label = $TopBar/LevelLabel
@onready var xp_bar: ProgressBar = $TopBar/XPBar
@onready var realm_label: Label = $TopBar/RealmLabel
@onready var streak_label: Label = $TopBar/StreakLabel
@onready var notification_panel: PanelContainer = $NotificationPanel
@onready var notification_label: Label = $NotificationPanel/Label

@onready var profile_button: Button = $NavBar/ProfileButton
@onready var feed_button: Button = $NavBar/FeedButton
@onready var chat_button: Button = $NavBar/ChatButton
@onready var settings_button: Button = $NavBar/SettingsButton

var _notification_timer := 0.0
var _notification_queue: Array[String] = []


func _ready() -> void:
	PlayerData.data_updated.connect(_update_display)
	GameManager.xp_earned.connect(_on_xp_earned)
	GameManager.level_up.connect(_on_level_up)
	GameManager.realm_entered.connect(_on_realm_entered)
	GameManager.achievement_earned.connect(_on_achievement_earned)

	profile_button.pressed.connect(func(): SceneManager.goto_scene("profile"))
	feed_button.pressed.connect(func(): SceneManager.goto_scene("feed"))
	chat_button.pressed.connect(func(): SceneManager.goto_scene("chat"))
	settings_button.pressed.connect(_on_settings)

	notification_panel.visible = false
	_update_display()


func _process(delta: float) -> void:
	if _notification_timer > 0:
		_notification_timer -= delta
		if _notification_timer <= 0:
			notification_panel.visible = false
			# Show next queued notification
			if _notification_queue.size() > 0:
				var next = _notification_queue.pop_front()
				_show_notification(next)


func _update_display() -> void:
	level_label.text = "Lv %d" % PlayerData.overall_level
	xp_bar.value = PlayerData.xp_progress_percent() * 100.0
	streak_label.text = "%d day streak" % PlayerData.streak_days if PlayerData.streak_days > 0 else ""


func _on_xp_earned(amount: int, _total: int) -> void:
	queue_notification("+%d XP" % amount)
	_update_display()


func _on_level_up(new_level: int) -> void:
	queue_notification("LEVEL UP! Now Level %d" % new_level)
	_update_display()


func _on_realm_entered(realm_slug: String) -> void:
	var realm_name = realm_slug.replace("_", " ").capitalize()
	realm_label.text = realm_name


func _on_achievement_earned(achievement: Dictionary) -> void:
	var title = achievement.get("title_en", "Achievement")
	var xp = achievement.get("xp_reward", 0)
	queue_notification("Achievement: %s (+%d XP)" % [title, xp])


func _on_settings() -> void:
	# Toggle mouse capture for settings access
	if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	else:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func queue_notification(text: String) -> void:
	if _notification_timer > 0:
		_notification_queue.append(text)
	else:
		_show_notification(text)


func _show_notification(text: String) -> void:
	notification_label.text = text
	notification_panel.visible = true
	_notification_timer = 3.0
