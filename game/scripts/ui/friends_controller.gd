extends Control
## Friends list and social features controller.

var _friends: Array = []
var _pending_requests: Array = []
var _search_results: Array = []

@onready var friends_list: Container = $FriendsList if has_node("FriendsList") else null
@onready var requests_list: Container = $RequestsList if has_node("RequestsList") else null
@onready var search_input: LineEdit = $SearchInput if has_node("SearchInput") else null
@onready var search_results: Container = $SearchResults if has_node("SearchResults") else null
@onready var status_label: Label = $StatusLabel if has_node("StatusLabel") else null
@onready var tab_container: TabContainer = $TabContainer if has_node("TabContainer") else null
@onready var back_button: Button = $BackButton if has_node("BackButton") else null


func _ready() -> void:
	_load_friends()
	_load_requests()
	if search_input:
		search_input.text_submitted.connect(_on_search)
	if back_button:
		back_button.pressed.connect(_on_back_pressed)


func _load_friends() -> void:
	print("[Friends] Loading friends list...")
	_show_status("Loading friends...")

	var result = await ApiClient.get("/friends/")
	if result.status == 200 and result.data:
		_friends = result.data.get("friends", [])
		_populate_friends_list()
		print("[Friends] Loaded %d friends" % _friends.size())
		_show_status("")
	elif result.status == 0:
		print("[Friends] Server unreachable while loading friends")
		_show_status("Could not load friends (offline)")
	else:
		print("[Friends] Failed to load friends — status %d" % result.status)
		_show_status("Failed to load friends")


func _load_requests() -> void:
	print("[Friends] Loading pending requests...")

	var result = await ApiClient.get("/friends/requests/")
	if result.status == 200 and result.data:
		_pending_requests = result.data.get("requests", [])
		_populate_requests_list()
		print("[Friends] Loaded %d pending requests" % _pending_requests.size())
	elif result.status == 0:
		print("[Friends] Server unreachable while loading requests")
	else:
		print("[Friends] Failed to load requests — status %d" % result.status)


func _on_search(query: String) -> void:
	var trimmed = query.strip_edges()
	if trimmed.is_empty():
		return

	print("[Friends] Searching players: %s" % trimmed)
	_show_status("Searching...")

	var result = await ApiClient.get("/accounts/search/?q=%s" % trimmed.uri_encode())
	if result.status == 200 and result.data:
		_search_results = result.data.get("results", [])
		_populate_search_results()
		print("[Friends] Found %d results" % _search_results.size())
		if _search_results.size() == 0:
			_show_status("No players found")
		else:
			_show_status("")
	elif result.status == 0:
		print("[Friends] Server unreachable during search")
		_show_status("Search failed (offline)")
	else:
		print("[Friends] Search failed — status %d" % result.status)
		_show_status("Search failed")


func _send_friend_request(player_id: int) -> void:
	print("[Friends] Sending friend request to player %d" % player_id)
	_show_status("Sending request...")

	var result = await ApiClient.post("/friends/request/", {"player_id": player_id})
	if result.status == 200 or result.status == 201:
		print("[Friends] Friend request sent to player %d" % player_id)
		_show_status("Friend request sent!")
	elif result.status == 0:
		print("[Friends] Server unreachable while sending request")
		_show_status("Could not send request (offline)")
	else:
		var msg = ""
		if result.data and result.data is Dictionary:
			msg = result.data.get("detail", result.data.get("error", ""))
		if msg.is_empty():
			msg = "Could not send request"
		print("[Friends] Failed to send request — status %d" % result.status)
		_show_status(msg)


func _respond_to_request(request_id: int, action: String) -> void:
	print("[Friends] Responding to request %d with action: %s" % [request_id, action])
	_show_status("Processing...")

	var result = await ApiClient.post("/friends/respond/", {
		"request_id": request_id,
		"action": action,
	})
	if result.status == 200 or result.status == 201:
		print("[Friends] Request %d — %s" % [request_id, action])
		if action == "accept":
			_show_status("Friend added!")
		else:
			_show_status("Request declined")
		# Refresh both lists
		_load_friends()
		_load_requests()
	elif result.status == 0:
		print("[Friends] Server unreachable while responding to request")
		_show_status("Could not respond (offline)")
	else:
		print("[Friends] Failed to respond to request — status %d" % result.status)
		_show_status("Failed to process request")


func _remove_friend(player_id: int) -> void:
	print("[Friends] Removing friend %d" % player_id)
	_show_status("Removing friend...")

	var result = await ApiClient.delete("/friends/%d/" % player_id)
	if result.status == 200 or result.status == 204:
		print("[Friends] Removed friend %d" % player_id)
		_show_status("Friend removed")
		_load_friends()
	elif result.status == 0:
		print("[Friends] Server unreachable while removing friend")
		_show_status("Could not remove friend (offline)")
	else:
		print("[Friends] Failed to remove friend — status %d" % result.status)
		_show_status("Failed to remove friend")


func _on_back_pressed() -> void:
	SceneManager.goto_scene("world_hub")


# ---------------------------------------------------------------------------
# UI builders
# ---------------------------------------------------------------------------

func _populate_friends_list() -> void:
	if not friends_list:
		return
	for child in friends_list.get_children():
		child.queue_free()
	for friend_data in _friends:
		friends_list.add_child(_create_friend_card(friend_data))


func _populate_requests_list() -> void:
	if not requests_list:
		return
	for child in requests_list.get_children():
		child.queue_free()
	for req_data in _pending_requests:
		requests_list.add_child(_create_request_card(req_data))


func _populate_search_results() -> void:
	if not search_results:
		return
	for child in search_results.get_children():
		child.queue_free()
	for player_data in _search_results:
		search_results.add_child(_create_search_result_card(player_data))


func _create_friend_card(friend_data: Dictionary) -> HBoxContainer:
	var card = HBoxContainer.new()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Display name
	var name_label = Label.new()
	name_label.text = PlayerData.localized(friend_data, "display_name",
		friend_data.get("display_name", "Player"))
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Level
	var level_label = Label.new()
	level_label.text = "Lv %d" % friend_data.get("level", 0)

	# ELO
	var elo_label = Label.new()
	elo_label.text = "ELO %d" % friend_data.get("elo", 0)

	# Remove button
	var remove_btn = Button.new()
	remove_btn.text = "Remove"
	var pid = friend_data.get("id", friend_data.get("player_id", 0))
	remove_btn.pressed.connect(_remove_friend.bind(pid))

	card.add_child(name_label)
	card.add_child(level_label)
	card.add_child(elo_label)
	card.add_child(remove_btn)
	return card


func _create_request_card(request_data: Dictionary) -> HBoxContainer:
	var card = HBoxContainer.new()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Sender name
	var sender = request_data.get("from_player", {})
	var name_label = Label.new()
	name_label.text = PlayerData.localized(sender, "display_name",
		sender.get("display_name", "Player"))
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Optional message
	var msg = request_data.get("message", "")
	if msg != "" and msg != null:
		var msg_label = Label.new()
		msg_label.text = msg
		msg_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.add_child(name_label)
		card.add_child(msg_label)
	else:
		card.add_child(name_label)

	# Accept button
	var accept_btn = Button.new()
	accept_btn.text = "Accept"
	var rid = request_data.get("id", request_data.get("request_id", 0))
	accept_btn.pressed.connect(_respond_to_request.bind(rid, "accept"))

	# Reject button
	var reject_btn = Button.new()
	reject_btn.text = "Reject"
	reject_btn.pressed.connect(_respond_to_request.bind(rid, "reject"))

	card.add_child(accept_btn)
	card.add_child(reject_btn)
	return card


func _create_search_result_card(player_data: Dictionary) -> HBoxContainer:
	var card = HBoxContainer.new()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Player name
	var name_label = Label.new()
	name_label.text = PlayerData.localized(player_data, "display_name",
		player_data.get("display_name", "Player"))
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Level
	var level_label = Label.new()
	level_label.text = "Lv %d" % player_data.get("level", 0)

	# Add friend button
	var add_btn = Button.new()
	add_btn.text = "Add Friend"
	var pid = player_data.get("id", player_data.get("player_id", 0))
	add_btn.pressed.connect(_send_friend_request.bind(pid))

	card.add_child(name_label)
	card.add_child(level_label)
	card.add_child(add_btn)
	return card


func _show_status(text: String) -> void:
	if status_label:
		status_label.text = text
