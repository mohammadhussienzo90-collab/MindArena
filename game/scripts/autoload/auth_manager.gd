extends Node
## JWT authentication manager. Autoload singleton.

signal logged_in()
signal logged_out()
signal auth_failed(reason: String)

var _access_token: String = ""
var _refresh_token: String = ""
var is_authenticated := false

const TOKEN_SAVE_PATH := "user://auth_tokens.cfg"


func _ready() -> void:
	_load_tokens()


func get_access_token() -> String:
	return _access_token


func login(username: String, password: String) -> Dictionary:
	var result = await ApiClient.post("/accounts/login/", {
		"username": username, "password": password,
	})
	if result.status == 200 and result.data:
		_access_token = result.data.get("access", "")
		_refresh_token = result.data.get("refresh", "")
		is_authenticated = true
		_save_tokens()
		logged_in.emit()
		return {"success": true}
	else:
		var msg = "Login failed"
		if result.data and result.data.has("detail"):
			msg = result.data.detail
		auth_failed.emit(msg)
		return {"success": false, "error": msg}


func register(username: String, email: String, password: String, display_name: String) -> Dictionary:
	var result = await ApiClient.post("/accounts/register/", {
		"username": username,
		"email": email,
		"password": password,
		"display_name": display_name,
	})
	if result.status == 201 and result.data:
		_access_token = result.data.get("tokens", {}).get("access", "")
		_refresh_token = result.data.get("tokens", {}).get("refresh", "")
		is_authenticated = true
		_save_tokens()
		logged_in.emit()
		return {"success": true}
	else:
		return {"success": false, "error": str(result.data)}


func logout() -> void:
	_access_token = ""
	_refresh_token = ""
	is_authenticated = false
	_delete_tokens()
	logged_out.emit()


func refresh_token() -> bool:
	if _refresh_token == "":
		return false
	var result = await ApiClient.post("/accounts/token/refresh/", {
		"refresh": _refresh_token,
	})
	if result.status == 200 and result.data:
		_access_token = result.data.get("access", "")
		_save_tokens()
		return true
	else:
		logout()
		return false


func _save_tokens() -> void:
	var config = ConfigFile.new()
	config.set_value("auth", "access", _access_token)
	config.set_value("auth", "refresh", _refresh_token)
	config.save(TOKEN_SAVE_PATH)


func _load_tokens() -> void:
	var config = ConfigFile.new()
	if config.load(TOKEN_SAVE_PATH) == OK:
		_access_token = config.get_value("auth", "access", "")
		_refresh_token = config.get_value("auth", "refresh", "")
		is_authenticated = _access_token != ""


func _delete_tokens() -> void:
	if FileAccess.file_exists(TOKEN_SAVE_PATH):
		DirAccess.remove_absolute(TOKEN_SAVE_PATH)
