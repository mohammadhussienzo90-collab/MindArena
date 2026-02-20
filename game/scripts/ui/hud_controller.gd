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
@onready var arena_button: Button = $NavBar/ArenaButton if has_node("NavBar/ArenaButton") else null
@onready var friends_button: Button = $NavBar/FriendsButton if has_node("NavBar/FriendsButton") else null
@onready var notif_badge: Label = $NavBar/NotifBadge if has_node("NavBar/NotifBadge") else null

var _notification_timer := 0.0
var _notification_queue: Array[String] = []
var _notif_poll_timer := 0.0
const NOTIF_POLL_INTERVAL := 30.0


func _ready() -> void:
	PlayerData.data_updated.connect(_update_display)
	GameManager.xp_earned.connect(_on_xp_earned)
	GameManager.level_up.connect(_on_level_up)
	GameManager.realm_entered.connect(_on_realm_entered)
	GameManager.achievement_earned.connect(_on_achievement_earned)
	ApiClient.connection_status_changed.connect(_on_connection_changed)

	profile_button.pressed.connect(func(): SceneManager.goto_scene("profile"))
	feed_button.pressed.connect(func(): SceneManager.goto_scene("feed"))
	chat_button.pressed.connect(func(): SceneManager.goto_scene("chat"))
	settings_button.pressed.connect(_on_settings)
	if arena_button:
		arena_button.pressed.connect(func(): SceneManager.goto_scene("arena"))
	if friends_button:
		friends_button.pressed.connect(func(): SceneManager.goto_scene("friends"))

	notification_panel.visible = false
	_update_display()
	_poll_notifications()


func _process(delta: float) -> void:
	if _notification_timer > 0:
		_notification_timer -= delta
		if _notification_timer <= 0:
			notification_panel.visible = false
			# Show next queued notification
			if _notification_queue.size() > 0:
				var next = _notification_queue.pop_front()
				_show_notification(next)

	# Poll for server notifications periodically
	_notif_poll_timer += delta
	if _notif_poll_timer >= NOTIF_POLL_INTERVAL:
		_notif_poll_timer = 0.0
		_poll_notifications()


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
	var title = PlayerData.localized(achievement, "title", "Achievement")
	var xp = achievement.get("xp_reward", 0)
	queue_notification("Achievement: %s (+%d XP)" % [title, xp])


func _on_settings() -> void:
	SceneManager.goto_scene("settings")


func _on_connection_changed(connected: bool) -> void:
	if connected:
		queue_notification("Connection restored")
	else:
		queue_notification("Connection lost — retrying...")


func queue_notification(text: String) -> void:
	if _notification_timer > 0:
		_notification_queue.append(text)
	else:
		_show_notification(text)


func _show_notification(text: String) -> void:
	notification_label.text = text
	notification_panel.visible = true
	_notification_timer = 3.0


func _poll_notifications() -> void:
	var result = await ApiClient.get("/notifications/?unread_only=true")
	if result.status == 200 and result.data != null:
		var unread_count = result.data.get("unread_count", 0)
		if notif_badge:
			notif_badge.visible = unread_count > 0
			notif_badge.text = str(unread_count) if unread_count <= 99 else "99+"
		# Show new notifications as toast messages
		var results = result.data.get("results", [])
		for notif in results:
			var title = PlayerData.localized(notif, "title", "")
			if title != "":
				queue_notification(title)
