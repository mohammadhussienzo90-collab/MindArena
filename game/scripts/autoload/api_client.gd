extends Node
## HTTP client for Django backend API. Autoload singleton.

signal request_completed(response: Dictionary)
signal request_failed(error: String)

var base_url: String = "http://localhost:8000/api/v1"
var _http: HTTPRequest


func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.timeout = 30.0


func _get_headers() -> PackedStringArray:
	var headers = PackedStringArray([
		"Content-Type: application/json",
		"Accept: application/json",
	])
	var token = AuthManager.get_access_token()
	if token != "":
		headers.append("Authorization: Bearer %s" % token)
	return headers


func get(endpoint: String) -> Dictionary:
	var url = base_url + endpoint
	var headers = _get_headers()

	var http = HTTPRequest.new()
	add_child(http)

	var error = http.request(url, headers, HTTPClient.METHOD_GET)
	if error != OK:
		http.queue_free()
		return {"error": "Request failed", "status": 0}

	var result = await http.request_completed
	http.queue_free()

	var status_code = result[1]
	var body = result[3].get_string_from_utf8()
	var json = JSON.new()
	json.parse(body)

	return {"status": status_code, "data": json.data}


func post(endpoint: String, data: Dictionary = {}) -> Dictionary:
	var url = base_url + endpoint
	var headers = _get_headers()
	var body = JSON.stringify(data)

	var http = HTTPRequest.new()
	add_child(http)

	var error = http.request(url, headers, HTTPClient.METHOD_POST, body)
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
