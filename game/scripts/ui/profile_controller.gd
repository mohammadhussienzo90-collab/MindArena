extends Control
## Profile screen — shows player stats, radar chart, realm progress, achievements.

@onready var player_name: Label = $ScrollContainer/VBoxContainer/PlayerName
@onready var level_label: Label = $ScrollContainer/VBoxContainer/LevelLabel
@onready var xp_bar: ProgressBar = $ScrollContainer/VBoxContainer/XPBar
@onready var streak_label: Label = $ScrollContainer/VBoxContainer/StreakLabel
@onready var radar_chart: Control = $ScrollContainer/VBoxContainer/RadarChart
@onready var realm_stats_container: VBoxContainer = $ScrollContainer/VBoxContainer/RealmStatsContainer
@onready var achievements_grid: GridContainer = $ScrollContainer/VBoxContainer/AchievementsGrid
@onready var back_button: Button = $BackButton


func _ready() -> void:
	back_button.pressed.connect(func(): SceneManager.goto_scene("world_hub"))
	_load_profile()


func _load_profile() -> void:
	# Player info from cached data
	player_name.text = PlayerData.display_name if PlayerData.display_name != "" else "Player"
	level_label.text = "Level %d — %d XP" % [PlayerData.overall_level, PlayerData.total_xp]

	# XP progress to next level
	xp_bar.max_value = 100.0
	xp_bar.value = PlayerData.xp_progress_percent() * 100.0

	streak_label.text = "Loading stats..."

	# Load stats from API
	var result = await ApiClient.get("/progression/stats/")
	if result.status == 200 and result.data:
		_populate_stats(result.data)
	elif result.status == 0:
		streak_label.text = "Could not load stats (offline)"
	else:
		streak_label.text = ""

	# Load achievements
	var ach_result = await ApiClient.get("/progression/achievements/earned/")
	if ach_result.status == 200 and ach_result.data:
		_populate_achievements(ach_result.data)


func _populate_stats(data: Dictionary) -> void:
	# Streak
	var streak = data.get("streak", {})
	if streak:
		streak_label.text = "%d Day Streak" % streak.get("current_streak", 0)
	else:
		streak_label.text = ""

	# Radar chart
	var realm_stats = data.get("realm_stats", [])
	if realm_stats.size() > 0:
		var labels: PackedStringArray = []
		var values: PackedFloat32Array = []
		for stat in realm_stats:
			labels.append(stat.get("realm_name", ""))
			values.append(float(stat.get("realm_level", 0)))
		radar_chart.set_data(labels, values)

	# Realm stat bars
	for child in realm_stats_container.get_children():
		child.queue_free()

	for stat in realm_stats:
		var hbox = HBoxContainer.new()
		var name_label = Label.new()
		name_label.text = stat.get("realm_name", "")
		name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var level_l = Label.new()
		level_l.text = "Lv %d" % stat.get("realm_level", 0)
		hbox.add_child(name_label)
		hbox.add_child(level_l)
		realm_stats_container.add_child(hbox)


func _populate_achievements(data: Array) -> void:
	for child in achievements_grid.get_children():
		child.queue_free()

	for ach in data:
		var ach_data = ach.get("achievement", {})
		var label = Label.new()
		label.text = PlayerData.localized(ach_data, "title", "?")
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		achievements_grid.add_child(label)
