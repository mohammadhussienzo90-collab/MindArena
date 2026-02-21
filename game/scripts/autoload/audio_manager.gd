extends Node
## Audio manager for music and SFX. Autoload singleton.

var music_player: AudioStreamPlayer
var sfx_player: AudioStreamPlayer
var music_volume: float = 0.8
var sfx_volume: float = 1.0
var music_enabled: bool = true
var sfx_enabled: bool = true

const SAVE_PATH := "user://audio_settings.cfg"


func _ready() -> void:
	music_player = AudioStreamPlayer.new()
	music_player.bus = "Music"
	add_child(music_player)

	sfx_player = AudioStreamPlayer.new()
	sfx_player.bus = "SFX"
	add_child(sfx_player)

	_load_settings()


func play_music(stream: AudioStream, fade_in := true) -> void:
	if not music_enabled:
		return
	music_player.stream = stream
	if fade_in:
		music_player.volume_db = linear_to_db(0.0)
		music_player.play()
		var tween = create_tween()
		tween.tween_property(music_player, "volume_db", linear_to_db(music_volume), 1.5)
	else:
		music_player.volume_db = linear_to_db(music_volume)
		music_player.play()


func stop_music() -> void:
	music_player.stop()


func play_sfx(stream: AudioStream) -> void:
	if not sfx_enabled:
		return
	sfx_player.stream = stream
	sfx_player.volume_db = linear_to_db(sfx_volume)
	sfx_player.play()


func set_music_volume(vol: float) -> void:
	music_volume = clamp(vol, 0.0, 1.0)
	music_player.volume_db = linear_to_db(music_volume)
	_save_settings()


func set_sfx_volume(vol: float) -> void:
	sfx_volume = clamp(vol, 0.0, 1.0)
	sfx_player.volume_db = linear_to_db(sfx_volume)
	_save_settings()


func _save_settings() -> void:
	var config = ConfigFile.new()
	config.set_value("audio", "music_volume", music_volume)
	config.set_value("audio", "sfx_volume", sfx_volume)
	config.set_value("audio", "music_enabled", music_enabled)
	config.set_value("audio", "sfx_enabled", sfx_enabled)
	config.save(SAVE_PATH)


func _load_settings() -> void:
	var config = ConfigFile.new()
	if config.load(SAVE_PATH) == OK:
		music_volume = config.get_value("audio", "music_volume", 0.8)
		sfx_volume = config.get_value("audio", "sfx_volume", 1.0)
		music_enabled = config.get_value("audio", "music_enabled", true)
		sfx_enabled = config.get_value("audio", "sfx_enabled", true)
