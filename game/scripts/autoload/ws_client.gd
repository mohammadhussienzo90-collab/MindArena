extends Node
## WebSocket client for real-time arena matches. Autoload singleton.
## Handles connection lifecycle, JSON messaging, and automatic reconnection.

signal connected()
signal disconnected()
signal message_received(data: Dictionary)
signal connection_error(error_msg: String)

var _socket: WebSocketPeer
var _url: String = ""
var _is_connected: bool = false
var _is_connecting: bool = false
var _reconnect_attempts: int = 0

const MAX_RECONNECT_ATTEMPTS := 3
const RECONNECT_DELAY := 2.0


func connect_to_match(match_id: int) -> void:
	"""Connect to an arena match WebSocket."""
	var token: String = AuthManager.get_access_token()
	var base_url: String = _get_ws_base_url()
	_url = "%s/ws/arena/%d/?token=%s" % [base_url, match_id, token]
	_start_connection()


func connect_to_matchmaking() -> void:
	"""Connect to the matchmaking WebSocket."""
	var token: String = AuthManager.get_access_token()
	var base_url: String = _get_ws_base_url()
	_url = "%s/ws/arena/matchmaking/?token=%s" % [base_url, token]
	_start_connection()


func send_json(data: Dictionary) -> void:
	"""Send a JSON message to the server."""
	if _socket and _is_connected:
		var text := JSON.stringify(data)
		_socket.send_text(text)


func close_connection() -> void:
	"""Gracefully close the WebSocket connection."""
	_reconnect_attempts = MAX_RECONNECT_ATTEMPTS  # Prevent auto-reconnect
	if _socket:
		_socket.close()
	_is_connected = false
	_is_connecting = false


func is_connected() -> bool:
	return _is_connected


func _start_connection() -> void:
	if _is_connecting:
		return

	_is_connecting = true
	_socket = WebSocketPeer.new()

	var err := _socket.connect_to_url(_url)
	if err != OK:
		_is_connecting = false
		connection_error.emit("Failed to initiate WebSocket connection (error %d)" % err)
		return

	print("[WsClient] Connecting to: %s" % _url.split("?")[0])


func _process(_delta: float) -> void:
	if _socket == null:
		return

	_socket.poll()
	var state := _socket.get_ready_state()

	match state:
		WebSocketPeer.STATE_OPEN:
			if not _is_connected:
				_is_connected = true
				_is_connecting = false
				_reconnect_attempts = 0
				connected.emit()
				print("[WsClient] Connected")

			# Process all available packets
			while _socket.get_available_packet_count() > 0:
				var packet := _socket.get_packet()
				var text := packet.get_string_from_utf8()
				var json := JSON.new()
				if json.parse(text) == OK and json.data is Dictionary:
					message_received.emit(json.data)
				else:
					push_warning("[WsClient] Invalid JSON received: %s" % text.substr(0, 100))

		WebSocketPeer.STATE_CLOSING:
			pass  # Wait for close

		WebSocketPeer.STATE_CLOSED:
			if _is_connected:
				_is_connected = false
				_is_connecting = false
				disconnected.emit()
				var code := _socket.get_close_code()
				print("[WsClient] Disconnected (code=%d)" % code)

				# Auto-reconnect if not intentionally closed
				if _reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
					_reconnect_attempts += 1
					print("[WsClient] Reconnecting (attempt %d/%d)..." % [
						_reconnect_attempts, MAX_RECONNECT_ATTEMPTS,
					])
					await get_tree().create_timer(RECONNECT_DELAY).timeout
					_start_connection()
			elif _is_connecting:
				_is_connecting = false
				connection_error.emit("Connection failed")

		WebSocketPeer.STATE_CONNECTING:
			pass  # Still connecting


func _get_ws_base_url() -> String:
	"""Convert the HTTP API base URL to a WebSocket URL."""
	var http_url: String = ApiClient.base_url if ApiClient else "http://localhost:8000/api/v1"
	# Strip /api/v1 suffix
	var base := http_url.replace("/api/v1", "")
	# Convert http(s) to ws(s)
	base = base.replace("https://", "wss://").replace("http://", "ws://")
	return base
