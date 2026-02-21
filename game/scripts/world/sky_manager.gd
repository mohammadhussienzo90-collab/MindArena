extends Node3D
class_name SkyManager
## Manages sky, atmosphere, and post-processing for the world hub and realm environments.
## Creates a WorldEnvironment with ProceduralSkyMaterial and realm-specific presets.
## Supports smooth transitions between environments when entering/leaving portals.

const TRANSITION_DURATION := 1.5

# Environment presets keyed by realm slug (or "hub" for the world hub)
var _presets: Dictionary = {}
var _world_env: WorldEnvironment
var _environment: Environment
var _current_preset: String = "hub"
var _transition_tween: Tween


func _ready() -> void:
	_init_presets()
	_build_environment("hub")


func transition_to(preset_key: String) -> void:
	if preset_key == _current_preset:
		return
	if not _presets.has(preset_key):
		preset_key = "hub"

	var target: Dictionary = _presets[preset_key]
	_current_preset = preset_key

	if _transition_tween and _transition_tween.is_valid():
		_transition_tween.kill()

	_transition_tween = create_tween()
	_transition_tween.set_parallel(true)
	_transition_tween.set_trans(Tween.TRANS_CUBIC)
	_transition_tween.set_ease(Tween.EASE_IN_OUT)

	# Animate sky
	var sky_mat: ProceduralSkyMaterial = _environment.sky.sky_material
	_transition_tween.tween_property(sky_mat, "sky_top_color", target.sky_top, TRANSITION_DURATION)
	_transition_tween.tween_property(sky_mat, "sky_horizon_color", target.sky_horizon, TRANSITION_DURATION)
	_transition_tween.tween_property(sky_mat, "ground_bottom_color", target.ground_bottom, TRANSITION_DURATION)
	_transition_tween.tween_property(sky_mat, "ground_horizon_color", target.ground_horizon, TRANSITION_DURATION)

	# Animate fog
	_transition_tween.tween_property(_environment, "fog_light_color", target.fog_color, TRANSITION_DURATION)
	_transition_tween.tween_property(_environment, "fog_density", target.fog_density, TRANSITION_DURATION)

	# Animate ambient
	_transition_tween.tween_property(_environment, "ambient_light_color", target.ambient_color, TRANSITION_DURATION)
	_transition_tween.tween_property(_environment, "ambient_light_energy", target.ambient_energy, TRANSITION_DURATION)

	# Animate glow
	_transition_tween.tween_property(_environment, "glow_intensity", target.glow_intensity, TRANSITION_DURATION)
	_transition_tween.tween_property(_environment, "glow_bloom", target.glow_bloom, TRANSITION_DURATION)


func get_environment() -> Environment:
	return _environment


func _build_environment(preset_key: String) -> void:
	var p: Dictionary = _presets.get(preset_key, _presets["hub"])
	_current_preset = preset_key

	_environment = Environment.new()

	# Sky
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = p.sky_top
	sky_mat.sky_horizon_color = p.sky_horizon
	sky_mat.ground_bottom_color = p.ground_bottom
	sky_mat.ground_horizon_color = p.ground_horizon
	sky_mat.sky_energy_multiplier = 1.0

	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_256
	_environment.sky = sky
	_environment.background_mode = Environment.BG_SKY

	# Ambient lighting
	_environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	_environment.ambient_light_color = p.ambient_color
	_environment.ambient_light_energy = p.ambient_energy

	# Fog
	_environment.fog_enabled = true
	_environment.fog_light_color = p.fog_color
	_environment.fog_density = p.fog_density
	_environment.fog_aerial_perspective = 0.3

	# Glow / Bloom
	_environment.glow_enabled = true
	_environment.glow_intensity = p.glow_intensity
	_environment.glow_bloom = p.glow_bloom
	_environment.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	_environment.glow_hdr_threshold = 0.8

	# Tonemap — filmic for cinematic feel
	_environment.tonemap_mode = Environment.TONE_MAP_FILMIC
	_environment.tonemap_exposure = p.get("exposure", 1.0)
	_environment.tonemap_white = 6.0

	# SSAO for depth
	_environment.ssao_enabled = true
	_environment.ssao_radius = 1.5
	_environment.ssao_intensity = 1.0

	# Create WorldEnvironment node
	_world_env = WorldEnvironment.new()
	_world_env.name = "WorldEnvironment"
	_world_env.environment = _environment
	add_child(_world_env)


func _init_presets() -> void:
	# Hub — deep space with mystical purple tones
	_presets["hub"] = {
		"sky_top": Color(0.02, 0.02, 0.08),
		"sky_horizon": Color(0.08, 0.04, 0.15),
		"ground_bottom": Color(0.01, 0.01, 0.03),
		"ground_horizon": Color(0.06, 0.03, 0.12),
		"fog_color": Color(0.06, 0.03, 0.1),
		"fog_density": 0.002,
		"ambient_color": Color(0.15, 0.1, 0.25),
		"ambient_energy": 0.4,
		"glow_intensity": 0.8,
		"glow_bloom": 0.3,
		"exposure": 1.1,
	}

	# Logic Fortress — crisp blue, clear, precise atmosphere
	_presets["logic_fortress"] = {
		"sky_top": Color(0.05, 0.1, 0.3),
		"sky_horizon": Color(0.1, 0.2, 0.5),
		"ground_bottom": Color(0.02, 0.03, 0.08),
		"ground_horizon": Color(0.05, 0.1, 0.2),
		"fog_color": Color(0.08, 0.12, 0.3),
		"fog_density": 0.001,
		"ambient_color": Color(0.2, 0.3, 0.6),
		"ambient_energy": 0.5,
		"glow_intensity": 1.0,
		"glow_bloom": 0.2,
		"exposure": 1.0,
	}

	# Emotion Ocean — misty cyan, ethereal, underwater feel
	_presets["emotion_ocean"] = {
		"sky_top": Color(0.02, 0.15, 0.2),
		"sky_horizon": Color(0.05, 0.25, 0.3),
		"ground_bottom": Color(0.0, 0.05, 0.1),
		"ground_horizon": Color(0.02, 0.15, 0.2),
		"fog_color": Color(0.05, 0.2, 0.25),
		"fog_density": 0.005,
		"ambient_color": Color(0.1, 0.3, 0.35),
		"ambient_energy": 0.5,
		"glow_intensity": 1.2,
		"glow_bloom": 0.4,
		"exposure": 1.0,
	}

	# Creativity Nebula — purple aurora, dreamlike
	_presets["creativity_nebula"] = {
		"sky_top": Color(0.15, 0.02, 0.25),
		"sky_horizon": Color(0.2, 0.08, 0.35),
		"ground_bottom": Color(0.05, 0.0, 0.1),
		"ground_horizon": Color(0.12, 0.04, 0.2),
		"fog_color": Color(0.12, 0.04, 0.18),
		"fog_density": 0.003,
		"ambient_color": Color(0.25, 0.1, 0.35),
		"ambient_energy": 0.45,
		"glow_intensity": 1.5,
		"glow_bloom": 0.5,
		"exposure": 1.1,
	}

	# Discipline Citadel — warm orange/amber, structured
	_presets["discipline_citadel"] = {
		"sky_top": Color(0.15, 0.08, 0.02),
		"sky_horizon": Color(0.3, 0.15, 0.05),
		"ground_bottom": Color(0.05, 0.03, 0.01),
		"ground_horizon": Color(0.15, 0.08, 0.03),
		"fog_color": Color(0.15, 0.1, 0.04),
		"fog_density": 0.002,
		"ambient_color": Color(0.35, 0.2, 0.1),
		"ambient_energy": 0.5,
		"glow_intensity": 0.7,
		"glow_bloom": 0.2,
		"exposure": 1.0,
	}

	# Knowledge Peaks — clear green/teal, alpine clarity
	_presets["knowledge_peaks"] = {
		"sky_top": Color(0.03, 0.12, 0.08),
		"sky_horizon": Color(0.08, 0.2, 0.15),
		"ground_bottom": Color(0.01, 0.04, 0.03),
		"ground_horizon": Color(0.05, 0.1, 0.08),
		"fog_color": Color(0.06, 0.12, 0.1),
		"fog_density": 0.003,
		"ambient_color": Color(0.15, 0.3, 0.2),
		"ambient_energy": 0.55,
		"glow_intensity": 0.6,
		"glow_bloom": 0.15,
		"exposure": 1.05,
	}

	# Social Bridge — warm orange sunset, inviting
	_presets["social_bridge"] = {
		"sky_top": Color(0.2, 0.1, 0.03),
		"sky_horizon": Color(0.4, 0.2, 0.08),
		"ground_bottom": Color(0.08, 0.04, 0.02),
		"ground_horizon": Color(0.2, 0.12, 0.05),
		"fog_color": Color(0.2, 0.12, 0.06),
		"fog_density": 0.002,
		"ambient_color": Color(0.4, 0.25, 0.15),
		"ambient_energy": 0.55,
		"glow_intensity": 0.9,
		"glow_bloom": 0.3,
		"exposure": 1.1,
	}

	# Wealth Garden — lush green with golden accents
	_presets["wealth_garden"] = {
		"sky_top": Color(0.05, 0.15, 0.05),
		"sky_horizon": Color(0.15, 0.25, 0.1),
		"ground_bottom": Color(0.02, 0.05, 0.02),
		"ground_horizon": Color(0.08, 0.15, 0.05),
		"fog_color": Color(0.08, 0.12, 0.05),
		"fog_density": 0.002,
		"ambient_color": Color(0.2, 0.35, 0.15),
		"ambient_energy": 0.55,
		"glow_intensity": 0.8,
		"glow_bloom": 0.25,
		"exposure": 1.0,
	}

	# Wellness Grove — soft magenta/pink, calming
	_presets["wellness_grove"] = {
		"sky_top": Color(0.1, 0.03, 0.08),
		"sky_horizon": Color(0.2, 0.1, 0.18),
		"ground_bottom": Color(0.03, 0.01, 0.03),
		"ground_horizon": Color(0.1, 0.05, 0.1),
		"fog_color": Color(0.1, 0.06, 0.1),
		"fog_density": 0.003,
		"ambient_color": Color(0.3, 0.15, 0.25),
		"ambient_energy": 0.5,
		"glow_intensity": 1.0,
		"glow_bloom": 0.35,
		"exposure": 1.0,
	}
