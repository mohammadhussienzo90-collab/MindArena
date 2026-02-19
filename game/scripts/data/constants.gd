extends Node
## Game-wide constants and configuration.

# API
const API_BASE_URL := "http://localhost:8000/api/v1"
const API_TIMEOUT := 30.0

# Realms
const REALM_SLUGS := [
	"logic_fortress", "emotion_ocean", "creativity_nebula",
	"discipline_citadel", "knowledge_peaks", "social_bridge",
	"wealth_garden", "wellness_grove",
]

const REALM_COLORS := {
	"logic_fortress": Color(0.2, 0.4, 0.9),
	"emotion_ocean": Color(0.0, 0.7, 0.8),
	"creativity_nebula": Color(0.7, 0.2, 0.9),
	"discipline_citadel": Color(0.8, 0.5, 0.1),
	"knowledge_peaks": Color(0.1, 0.6, 0.3),
	"social_bridge": Color(0.9, 0.6, 0.2),
	"wealth_garden": Color(0.2, 0.7, 0.2),
	"wellness_grove": Color(0.4, 0.8, 0.6),
}

const REALM_NAMES := {
	"logic_fortress": "Logic Fortress",
	"emotion_ocean": "Emotion Ocean",
	"creativity_nebula": "Creativity Nebula",
	"discipline_citadel": "Discipline Citadel",
	"knowledge_peaks": "Knowledge Peaks",
	"social_bridge": "Social Bridge",
	"wealth_garden": "Wealth Garden",
	"wellness_grove": "Wellness Grove",
}

# XP
const XP_CURVE_EXPONENT := 1.5
const XP_BASE := 100

# Visual stages
const VISUAL_STAGE_THRESHOLDS := [0, 3, 6, 10, 15, 20]

# Player movement
const PLAYER_SPEED := 5.0
const PLAYER_SPRINT_MULTIPLIER := 1.8
const PLAYER_JUMP_VELOCITY := 4.5
const GRAVITY := 9.8
const MOUSE_SENSITIVITY := 0.003

# Camera
const CAMERA_MIN_PITCH := -89.0
const CAMERA_MAX_PITCH := 89.0
