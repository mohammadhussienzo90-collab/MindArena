extends Node
## Player data cache. Autoload singleton.

signal data_updated()
signal realm_stat_updated(realm_slug: String)

var display_name: String = ""
var overall_level: int = 1
var total_xp: int = 0
var onboarding_done: bool = false
var preferred_lang: String = "en"
var realm_stats: Dictionary = {}
var personality_traits: Dictionary = {}
var streak_days: int = 0


func load_profile() -> void:
	var result = await ApiClient.get("/accounts/profile/")
	if result.status == 200 and result.data:
		var d = result.data
		display_name = d.get("display_name", "")
		overall_level = d.get("overall_level", 1)
		total_xp = d.get("total_xp", 0)
		onboarding_done = d.get("onboarding_done", false)
		preferred_lang = d.get("preferred_lang", "en")
		data_updated.emit()


func load_realm_stats() -> void:
	var result = await ApiClient.get("/progression/progression/stats/")
	if result.status == 200 and result.data:
		for stat in result.data.get("realm_stats", []):
			realm_stats[stat.get("realm_slug", "")] = {
				"level": stat.get("realm_level", 1),
				"xp": stat.get("realm_xp", 0),
				"visual_stage": stat.get("visual_stage", 0),
				"challenges_completed": stat.get("challenges_completed", 0),
			}
		var streak_data = result.data.get("streak")
		if streak_data:
			streak_days = streak_data.get("current_streak", 0)
		data_updated.emit()


func get_realm_visual_stage(realm_slug: String) -> int:
	if realm_stats.has(realm_slug):
		return realm_stats[realm_slug].get("visual_stage", 0)
	return 0


func xp_for_level(level: int) -> int:
	return int(floor(100.0 * pow(level, 1.5)))


func xp_progress_percent() -> float:
	var current_level_xp = xp_for_level(overall_level)
	var next_level_xp = xp_for_level(overall_level + 1)
	var range_xp = next_level_xp - current_level_xp
	if range_xp <= 0:
		return 1.0
	return float(total_xp - current_level_xp) / float(range_xp)
