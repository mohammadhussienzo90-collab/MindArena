extends Node
class_name DialogueManager
## Signal-based dialogue system for MindArena narrative.
## Supports sequential lines, branching choices, and speaker identification.
## Dialogue data comes from Quest.intro_dialogue/outro_dialogue JSON or hardcoded story data.

signal dialogue_started(dialogue_id: String)
signal dialogue_line(speaker: String, text: String, options: Array)
signal dialogue_ended(dialogue_id: String)

var _current_dialogue_id: String = ""
var _current_lines: Array = []
var _current_index: int = 0
var _is_active: bool = false
var _waiting_for_choice: bool = false

# Built-in story dialogues (used when API data is not available)
var _story_dialogues: Dictionary = {}


func _ready() -> void:
	_init_story_dialogues()


func is_active() -> bool:
	return _is_active


func start_dialogue(dialogue_id: String, lines: Array = []) -> void:
	"""Start a dialogue sequence. If lines are empty, uses built-in story data."""
	if _is_active:
		return

	if lines.size() > 0:
		_current_lines = lines
	elif _story_dialogues.has(dialogue_id):
		_current_lines = _story_dialogues[dialogue_id]
	else:
		push_warning("[DialogueManager] No dialogue found for: %s" % dialogue_id)
		return

	_current_dialogue_id = dialogue_id
	_current_index = 0
	_is_active = true
	_waiting_for_choice = false
	dialogue_started.emit(dialogue_id)
	_show_current_line()


func advance(choice_index: int = -1) -> void:
	"""Advance to next line. Pass choice_index if the current line had options."""
	if not _is_active:
		return

	if _waiting_for_choice and choice_index < 0:
		return  # Must pick a choice

	_waiting_for_choice = false
	_current_index += 1

	if _current_index >= _current_lines.size():
		_end_dialogue()
		return

	_show_current_line()


func skip() -> void:
	"""Skip entire dialogue."""
	if _is_active:
		_end_dialogue()


func _show_current_line() -> void:
	var line: Dictionary = _current_lines[_current_index]
	var speaker: String = line.get("speaker", "Noor")
	var text: String = _localize(line, "text")
	var options: Array = line.get("options", [])

	if options.size() > 0:
		_waiting_for_choice = true

	dialogue_line.emit(speaker, text, options)


func _end_dialogue() -> void:
	_is_active = false
	_waiting_for_choice = false
	var id := _current_dialogue_id
	_current_dialogue_id = ""
	_current_lines = []
	_current_index = 0
	dialogue_ended.emit(id)


func _localize(data: Dictionary, field: String) -> String:
	var lang: String = PlayerData.preferred_lang if PlayerData.preferred_lang != "" else "en"
	var key: String = field + "_" + lang
	var value = data.get(key, "")
	if value == "" or value == null:
		value = data.get(field + "_en", data.get(field, ""))
	return str(value) if value != null else ""


func _init_story_dialogues() -> void:
	# === INTRO CINEMATIC DIALOGUE ===
	_story_dialogues["intro"] = [
		{"speaker": "???", "text_en": "Your mind... something has shattered it.", "text_ar": "عقلك... شيء ما حطمه."},
		{"speaker": "???", "text_en": "Eight fragments. Eight pieces of who you were.", "text_ar": "ثمان شظايا. ثمان قطع مما كنته."},
		{"speaker": "Noor", "text_en": "I am Noor. I survived the shattering.", "text_ar": "أنا نور. نجوت من التحطم."},
		{"speaker": "Noor", "text_en": "I am the part of you that remembers — your inner wisdom.", "text_ar": "أنا الجزء منك الذي يتذكر — حكمتك الداخلية."},
		{"speaker": "Noor", "text_en": "Each realm holds a piece of your true self. Logic. Emotion. Creativity. Discipline.", "text_ar": "كل عالم يحمل قطعة من ذاتك الحقيقية. المنطق. العاطفة. الإبداع. الانضباط."},
		{"speaker": "Noor", "text_en": "Knowledge. Connection. Abundance. Wellness.", "text_ar": "المعرفة. التواصل. الوفرة. العافية."},
		{"speaker": "Noor", "text_en": "Together, we will rebuild your mind. Stronger than before.", "text_ar": "معًا، سنعيد بناء عقلك. أقوى مما كان."},
		{
			"speaker": "Noor",
			"text_en": "Are you ready to begin?",
			"text_ar": "هل أنت مستعد للبدء؟",
			"options": [
				{"text_en": "I'm ready.", "text_ar": "أنا مستعد."},
				{"text_en": "Tell me more.", "text_ar": "أخبرني المزيد."},
			]
		},
	]

	# === REALM INTRO DIALOGUES ===
	_story_dialogues["realm_logic_fortress"] = [
		{"speaker": "Noor", "text_en": "The Logic Fortress. Where reason reigns supreme.", "text_ar": "قلعة المنطق. حيث يسود العقل."},
		{"speaker": "Noor", "text_en": "Your analytical mind was always your greatest weapon. Let's sharpen it.", "text_ar": "عقلك التحليلي كان دائمًا أقوى أسلحتك. دعنا نشحذه."},
		{"speaker": "Noor", "text_en": "Solve the challenges ahead. Each one rebuilds a piece of your logical foundation.", "text_ar": "حل التحديات أمامك. كل واحد يعيد بناء جزء من أساسك المنطقي."},
	]

	_story_dialogues["realm_emotion_ocean"] = [
		{"speaker": "Noor", "text_en": "The Emotion Ocean. Vast, deep, and powerful.", "text_ar": "محيط العاطفة. واسع وعميق وقوي."},
		{"speaker": "Noor", "text_en": "Understanding feelings — yours and others' — is not weakness. It is strength.", "text_ar": "فهم المشاعر — مشاعرك ومشاعر الآخرين — ليس ضعفًا. إنه قوة."},
		{"speaker": "Noor", "text_en": "Dive deep. The treasures of emotional intelligence await.", "text_ar": "غص عميقًا. كنوز الذكاء العاطفي بانتظارك."},
	]

	_story_dialogues["realm_creativity_nebula"] = [
		{"speaker": "Noor", "text_en": "The Creativity Nebula. Where imagination takes form.", "text_ar": "سديم الإبداع. حيث يتجسد الخيال."},
		{"speaker": "Noor", "text_en": "Here, there are no wrong answers. Only unexplored possibilities.", "text_ar": "هنا، لا توجد إجابات خاطئة. فقط احتمالات غير مستكشفة."},
		{"speaker": "Noor", "text_en": "Think differently. That's where breakthroughs live.", "text_ar": "فكر بشكل مختلف. هناك تعيش الاختراقات."},
	]

	_story_dialogues["realm_discipline_citadel"] = [
		{"speaker": "Noor", "text_en": "The Discipline Citadel. Built by willpower, stone by stone.", "text_ar": "قلعة الانضباط. بُنيت بالإرادة، حجرًا حجرًا."},
		{"speaker": "Noor", "text_en": "Every habit, every routine — they're the bricks of who you become.", "text_ar": "كل عادة، كل روتين — هي لبنات من تصبح."},
		{"speaker": "Noor", "text_en": "Master yourself, and the world follows.", "text_ar": "أتقن نفسك، والعالم يتبع."},
	]

	_story_dialogues["realm_knowledge_peaks"] = [
		{"speaker": "Noor", "text_en": "The Knowledge Peaks. The highest point in the Mindscape.", "text_ar": "قمم المعرفة. أعلى نقطة في عالم العقل."},
		{"speaker": "Noor", "text_en": "From up here, you can see how everything connects.", "text_ar": "من هنا يمكنك رؤية كيف يرتبط كل شيء."},
		{"speaker": "Noor", "text_en": "Understanding how your mind works is the ultimate power.", "text_ar": "فهم كيف يعمل عقلك هو القوة المطلقة."},
	]

	_story_dialogues["realm_social_bridge"] = [
		{"speaker": "Noor", "text_en": "The Social Bridge. No one rebuilds their mind alone.", "text_ar": "جسر التواصل. لا أحد يعيد بناء عقله وحده."},
		{"speaker": "Noor", "text_en": "Communication, empathy, leadership — these are the bridges between souls.", "text_ar": "التواصل، التعاطف، القيادة — هذه هي الجسور بين الأرواح."},
		{"speaker": "Noor", "text_en": "Cross this bridge, and you'll never walk alone again.", "text_ar": "اعبر هذا الجسر، ولن تمشي وحيدًا مرة أخرى."},
	]

	_story_dialogues["realm_wealth_garden"] = [
		{"speaker": "Noor", "text_en": "The Wealth Garden. Where patience grows fortune.", "text_ar": "حديقة الثروة. حيث ينمي الصبر الثروة."},
		{"speaker": "Noor", "text_en": "True wealth isn't just money. It's understanding how value flows.", "text_ar": "الثروة الحقيقية ليست مالًا فقط. إنها فهم كيف تتدفق القيمة."},
		{"speaker": "Noor", "text_en": "Plant seeds of knowledge. The harvest will come.", "text_ar": "ازرع بذور المعرفة. سيأتي الحصاد."},
	]

	_story_dialogues["realm_wellness_grove"] = [
		{"speaker": "Noor", "text_en": "The Wellness Grove. The most peaceful place in your mind.", "text_ar": "بستان العافية. أكثر الأماكن سلامًا في عقلك."},
		{"speaker": "Noor", "text_en": "A strong mind needs a strong body and a calm spirit.", "text_ar": "العقل القوي يحتاج جسدًا قويًا وروحًا هادئة."},
		{"speaker": "Noor", "text_en": "Rest, breathe, restore. Then you can face anything.", "text_ar": "استرح، تنفس، تعاف. بعدها يمكنك مواجهة أي شيء."},
	]
