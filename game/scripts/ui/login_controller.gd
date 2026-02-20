extends Control
## Login/Register screen controller.

@onready var username_edit: LineEdit = $VBoxContainer/UsernameEdit
@onready var password_edit: LineEdit = $VBoxContainer/PasswordEdit
@onready var login_button: Button = $VBoxContainer/LoginButton
@onready var register_button: Button = $VBoxContainer/RegisterButton
@onready var status_label: Label = $VBoxContainer/StatusLabel


func _ready() -> void:
	login_button.pressed.connect(_on_login)
	register_button.pressed.connect(_on_register)
	password_edit.text_submitted.connect(func(_t): _on_login())
	status_label.text = ""

	# Skip to hub if already logged in
	if AuthManager.is_authenticated:
		SceneManager.goto_scene("world_hub")


func _on_login() -> void:
	var username = username_edit.text.strip_edges()
	var password = password_edit.text

	if username.is_empty() or password.is_empty():
		_show_error("Please enter username and password.")
		return

	_set_loading(true)
	var result = await AuthManager.login(username, password)

	if result.get("success", false):
		await PlayerData.load_profile()
		status_label.add_theme_color_override("font_color", Color(0.4, 1, 0.4, 1))
		status_label.text = "Welcome back!"
		await get_tree().create_timer(0.5).timeout
		_go_to_next_scene()
	else:
		_show_error(result.get("error", "Login failed."))
		_set_loading(false)


func _on_register() -> void:
	var username = username_edit.text.strip_edges()
	var password = password_edit.text

	if username.length() < 3:
		_show_error("Username must be at least 3 characters.")
		return
	if password.length() < 6:
		_show_error("Password must be at least 6 characters.")
		return

	_set_loading(true)
	var result = await AuthManager.register(username, "", password, username)

	if result.get("success", false):
		await PlayerData.load_profile()
		status_label.add_theme_color_override("font_color", Color(0.4, 1, 0.4, 1))
		status_label.text = "Account created!"
		await get_tree().create_timer(0.5).timeout
		_go_to_next_scene()
	else:
		_show_error(result.get("error", "Registration failed."))
		_set_loading(false)


func _go_to_next_scene() -> void:
	# New users go to assessment, returning users go to hub
	if PlayerData.onboarding_done:
		SceneManager.goto_scene("world_hub")
	else:
		SceneManager.goto_scene("assessment")


func _show_error(msg: String) -> void:
	status_label.add_theme_color_override("font_color", Color(1, 0.4, 0.4, 1))
	status_label.text = msg


func _set_loading(loading: bool) -> void:
	login_button.disabled = loading
	register_button.disabled = loading
	username_edit.editable = not loading
	password_edit.editable = not loading
	if loading:
		status_label.text = "..."
