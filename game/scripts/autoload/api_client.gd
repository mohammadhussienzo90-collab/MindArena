extends Node
## HTTP client for Django backend API. Autoload singleton.

signal request_completed(response: Dictionary)
signal request_failed(error: String)
signal connection_status_changed(is_connected: bool)

var base_url: String = "http://localhost:8000/api/v1"
var is_connected: bool = true
var _consecutive_failures: int = 0

const CONFIG_PATH := "user://server_config.cfg"
const MAX_RETRIES := 2
const RETRY_DELAY_SECS := 1.0


func _ready() -> void:
	_load_server_config()


func _load_server_config() -> void:
	var config = ConfigFile.new()
	if config.load(CONFIG_PATH) == OK:
		base_url = config.get_value("server", "base_url", base_url)
	# Also check command-line override: --server=https://api.mindarena.com/api/v1
	for arg in OS.get_cmdline_args():
		if arg.begins_with("--server="):
			base_url = arg.substr(9)


func _get_headers() -> PackedStringArray:
	var headers = PackedStringArray([
		"Content-Type: application/json",
		"Accept: application/json",
	])
	var token = AuthManager.get_access_token()
	if token != "":
		headers.append("Authorization: Bearer %s" % token)
	return headers


func get(endpoint: String, _allow_retry: bool = true) -> Dictionary:
	var result = await _do_request(HTTPClient.METHOD_GET, endpoint, "")
	if result.status == 401 and _allow_retry:
		var refreshed = await AuthManager.refresh_token()
		if refreshed:
			return await get(endpoint, false)
	return result


func post(endpoint: String, data: Dictionary = {}, _allow_retry: bool = true) -> Dictionary:
	var body = JSON.stringify(data)
	var result = await _do_request(HTTPClient.METHOD_POST, endpoint, body)
	if result.status == 401 and _allow_retry:
		var refreshed = await AuthManager.refresh_token()
		if refreshed:
			return await post(endpoint, data, false)
	return result


func patch(endpoint: String, data: Dictionary = {}, _allow_retry: bool = true) -> Dictionary:
	var body = JSON.stringify(data)
	var result = await _do_request(HTTPClient.METHOD_PATCH, endpoint, body)
	if result.status == 401 and _allow_retry:
		var refreshed = await AuthManager.refresh_token()
		if refreshed:
			return await patch(endpoint, data, false)
	return result


func put(endpoint: String, data: Dictionary = {}, _allow_retry: bool = true) -> Dictionary:
	var body = JSON.stringify(data)
	var result = await _do_request(HTTPClient.METHOD_PUT, endpoint, body)
	if result.status == 401 and _allow_retry:
		var refreshed = await AuthManager.refresh_token()
		if refreshed:
			return await put(endpoint, data, false)
	return result


func delete(endpoint: String, _allow_retry: bool = true) -> Dictionary:
	var result = await _do_request(HTTPClient.METHOD_DELETE, endpoint, "")
	if result.status == 401 and _allow_retry:
		var refreshed = await AuthManager.refresh_token()
		if refreshed:
			return await delete(endpoint, false)
	return result


func _do_request(method: int, endpoint: String, body: String, _retry_count: int = 0) -> Dictionary:
	var url = base_url + endpoint
	var headers = _get_headers()

	var http = HTTPRequest.new()
	http.timeout = 15.0
	add_child(http)

	var error: int
	if body.is_empty():
		error = http.request(url, headers, method)
	else:
		error = http.request(url, headers, method, body)

	if error != OK:
		http.queue_free()
		_on_request_failed()
		if _retry_count < MAX_RETRIES:
			await get_tree().create_timer(RETRY_DELAY_SECS).timeout
			return await _do_request(method, endpoint, body, _retry_count + 1)
		return {"error": "Request failed", "status": 0}

	var result = await http.request_completed
	http.queue_free()

	var status_code = result[1]
	var response_body = result[3].get_string_from_utf8()

	# Handle network-level failures (status 0 = no response)
	if status_code == 0:
		_on_request_failed()
		if _retry_count < MAX_RETRIES:
			await get_tree().create_timer(RETRY_DELAY_SECS).timeout
			return await _do_request(method, endpoint, body, _retry_count + 1)
		return {"error": "Server unreachable", "status": 0}

	# Success — reset connection status
	_on_request_succeeded()

	var json = JSON.new()
	var parse_err = json.parse(response_body)
	if parse_err != OK:
		return {"status": status_code, "data": null}

	return {"status": status_code, "data": json.data}


func _on_request_failed() -> void:
	_consecutive_failures += 1
	if is_connected and _consecutive_failures >= 2:
		is_connected = false
		connection_status_changed.emit(false)
		request_failed.emit("Connection lost")
		print("[ApiClient] Connection lost after %d consecutive failures" % _consecutive_failures)


func _on_request_succeeded() -> void:
	_consecutive_failures = 0
	if not is_connected:
		is_connected = true
		connection_status_changed.emit(true)
		print("[ApiClient] Connection restored")
