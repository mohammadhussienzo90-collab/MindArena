extends Control
## Settings screen — language, logout, server info.

@onready var lang_button: Button = $VBoxContainer/LanguageHBox/LangButton
@onready var lang_label: Label = $VBoxContainer/LanguageHBox/LangLabel
@onready var server_label: Label = $VBoxContainer/ServerLabel
@onready var version_label: Label = $VBoxContainer/VersionLabel
@onready var logout_button: Button = $VBoxContainer/LogoutButton
@onready var back_button: Button = $BackButton

const VERSION := "1.0.0"


func _ready() -> void:
	back_button.pressed.connect(func(): SceneManager.goto_scene("world_hub"))
	logout_button.pressed.connect(_on_logout)
	lang_button.pressed.connect(_on_toggle_language)

	_update_lang_display()
	server_label.text = "Server: %s" % ApiClient.base_url
	version_label.text = "MindArena v%s" % VERSION


func _update_lang_display() -> void:
	var lang = PlayerData.preferred_lang
	if lang == "ar":
		lang_label.text = "Language: Arabic"
		lang_button.text = "Switch to English"
	else:
		lang_label.text = "Language: English"
		lang_button.text = "Switch to Arabic"


func _on_toggle_language() -> void:
	var new_lang = "ar" if PlayerData.preferred_lang == "en" else "en"
	PlayerData.preferred_lang = new_lang

	# Persist to server
	var result = await ApiClient.patch("/accounts/profile/", {"preferred_lang": new_lang})
	if result.status != 200:
		# Revert on failure
		PlayerData.preferred_lang = "en" if new_lang == "ar" else "ar"

	_update_lang_display()


func _on_logout() -> void:
	AuthManager.logout()
	SceneManager.goto_scene("login")
