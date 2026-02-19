extends CanvasLayer
## In-game HUD: XP bar, level, realm info, streak, quick actions.

@onready var level_label: Label = $TopBar/LevelLabel
@onready var xp_bar: ProgressBar = $TopBar/XPBar
@onready var realm_label: Label = $TopBar/RealmLabel
@onready var streak_label: Label = $TopBar/StreakLabel
@onready var notification_panel: PanelContainer = $NotificationPanel
@onready var notification_label: Label = $NotificationPanel/Label

var _notification_timer := 0.0


func _ready() -> void:
	PlayerData.data_updated.connect(_update_display)
	GameManager.xp_earned.connect(_on_xp_earned)
	GameManager.level_up.connect(_on_level_up)
	GameManager.realm_entered.connect(_on_realm_entered)

	notification_panel.visible = false
	_update_display()


func _process(delta: float) -> void:
	if _notification_timer > 0:
		_notification_timer -= delta
		if _notification_timer <= 0:
			notification_panel.visible = false


func _update_display() -> void:
	level_label.text = "Lv %d" % PlayerData.overall_level
	xp_bar.value = PlayerData.xp_progress_percent() * 100.0
	streak_label.text = "%d day streak" % PlayerData.streak_days if PlayerData.streak_days > 0 else ""


func _on_xp_earned(amount: int, _total: int) -> void:
	_show_notification("+%d XP" % amount)
	_update_display()


func _on_level_up(new_level: int) -> void:
	_show_notification("LEVEL UP! Now Level %d" % new_level)
	_update_display()


func _on_realm_entered(realm_slug: String) -> void:
	var realm_name = realm_slug.replace("_", " ").capitalize()
	realm_label.text = realm_name


func _show_notification(text: String) -> void:
	notification_label.text = text
	notification_panel.visible = true
	_notification_timer = 3.0
