extends Node
## HTTP client for Django backend API. Autoload singleton.

signal request_completed(response: Dictionary)
signal request_failed(error: String)

var base_url: String = "http://localhost:8000/api/v1"
var _http: HTTPRequest

const CONFIG_PATH := "user://server_config.cfg"


func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.timeout = 30.0
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


func _do_request(method: int, endpoint: String, body: String) -> Dictionary:
	var url = base_url + endpoint
	var headers = _get_headers()

	var http = HTTPRequest.new()
	add_child(http)

	var error: int
	if body.is_empty():
		error = http.request(url, headers, method)
	else:
		error = http.request(url, headers, method, body)

	if error != OK:
		http.queue_free()
		return {"error": "Request failed", "status": 0}

	var result = await http.request_completed
	http.queue_free()

	var status_code = result[1]
	var response_body = result[3].get_string_from_utf8()
	var json = JSON.new()
	json.parse(response_body)

	return {"status": status_code, "data": json.data}
