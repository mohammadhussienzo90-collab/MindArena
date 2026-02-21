"""
Smart Noor Response Templates
==============================
500+ response templates organized by category, supporting personality-based
filtering and placeholder substitution.

Placeholders
-------------
- ``{name}`` -- player display name
- ``{level}`` -- player's overall level
- ``{streak}`` -- current daily streak count
- ``{xp}`` -- total XP earned
- ``{realm}`` -- current realm name
- ``{realm_level}`` -- player's level in current realm
- ``{accuracy}`` -- session accuracy percentage
- ``{time_of_day}`` -- morning/afternoon/evening/night

Personality Matching
---------------------
Some templates include a ``personality_match`` dict that maps Big Five traits
to minimum threshold values. Positive values mean "high in this trait",
negative values mean "low in this trait" (inverted: e.g., -60 neuroticism
means the player's neuroticism must be BELOW 40).

This allows Noor to speak differently to introverts vs extroverts, etc.
"""

# ====================================================================== #
#                         TEMPLATES DICTIONARY                            #
# ====================================================================== #

TEMPLATES = {

    # ================================================================== #
    # 1. GREETING (40 templates)
    # ================================================================== #
    'greeting': [
        "Hey {name}! Ready to train your mind today?",
        "Welcome back, {name}! Level {level} looks good on you.",
        "Good {time_of_day}, {name}! Your {streak}-day streak is still going strong.",
        "{name}! I was wondering when you'd show up. Let's get started.",
        "Hey there, champion! Level {level} and climbing. What shall we tackle today?",
        "Welcome back to MindArena, {name}. Your brain called -- it wants a workout.",
        "Good {time_of_day}! You've got {xp} XP already. Let's add to that.",
        "{name}, reporting for duty! What realm are you feeling today?",
        "There you are! I've been saving some great challenges for you, {name}.",
        "Hey {name}! Another day, another opportunity to level up.",
        "Good to see you, {name}. The realms have been waiting for you.",
        "Welcome back, warrior! Your {streak}-day streak says you mean business.",
        "{name}! Perfect timing. I just found some challenges that match your skill level.",
        "Hey! Level {level}, {xp} XP, {streak}-day streak -- you're a machine, {name}.",
        "Good {time_of_day}, {name}. Ready to make today count?",
        "You're back! I've been analyzing your progress and I'm impressed, {name}.",
        "Hey {name}! Quick question -- are you ready to surprise yourself today?",
        "Welcome, {name}! The arena is buzzing and the challenges are fresh.",
        "Good {time_of_day}! Your mind is your most powerful tool, {name}. Let's sharpen it.",
        "{name} is in the building! Let's make this session legendary.",
        # Personality-matched greetings
        {'text': "Hey {name}! Want to explore something totally new today? I found some fascinating challenges.", 'personality_match': {'openness': 65}},
        {'text': "Welcome back, {name}. I've organized your progress neatly -- everything is on track.", 'personality_match': {'conscientiousness': 65}},
        {'text': "{name}! Great to have you back! Want to challenge some friends or hit the arena?", 'personality_match': {'extraversion': 65}},
        {'text': "Hey {name}. Welcome back. Take your time settling in -- no rush today.", 'personality_match': {'extraversion': -65}},
        {'text': "{name}! You're back! I know some players who'd love to team up with you today.", 'personality_match': {'agreeableness': 65}},
        {'text': "Welcome back, {name}. I've set up the most efficient path for your session today.", 'personality_match': {'conscientiousness': 70}},
        {'text': "Hey {name}! I have some creative challenges that I think you'll love.", 'personality_match': {'openness': 70, 'creative_thinking': 60}},
        {'text': "Good {time_of_day}, {name}. Remember: this is YOUR pace, YOUR journey.", 'personality_match': {'neuroticism': 60}},
        # Arabic bilingual greetings
        "Ahlan {name}! Welcome back to MindArena.",
        "Marhaba {name}! Level {level} and beyond.",
        "As-salamu alaykum, {name}! Ready for today's challenges?",
        "Ya {name}! Good to see you. Your streak of {streak} days is inspiring.",
        "Ahlan wa sahlan! Level {level}, {xp} XP -- mashallah, {name}!",
        "Sabah el-kheir, {name}! A {time_of_day} workout for the mind.",
        "Yalla {name}! Let's crush some challenges today.",
        "Welcome, {name}. In Arabic we say 'el-ilm noor' -- knowledge is light. Let's find some.",
        "Hey {name}! Bismillah -- let's start strong today.",
        "Marhaba! {name}, your {streak}-day streak -- tabarak allah!",
        "{name}! Hayyak allah. Ready for another session?",
        "Good {time_of_day}, {name}! Level {level} warrior checking in. The realms are ready for you.",
    ],

    # ================================================================== #
    # 2. ENCOURAGEMENT (50 templates)
    # ================================================================== #
    'encouragement': [
        "That was brilliant, {name}! You nailed that one.",
        "Look at you go! {xp} XP and counting.",
        "You're getting sharper with every challenge, {name}.",
        "That answer showed real depth of thinking. Impressive.",
        "Streak of {streak} days! Consistency is the key to mastery, and you've got it.",
        "{name}, you just made that look easy. It wasn't -- you've genuinely improved.",
        "Your accuracy in {realm} is climbing. I can literally see you getting smarter.",
        "That's the kind of answer that separates good players from great ones.",
        "Level {level} and you're still accelerating. Most players plateau by now.",
        "Every correct answer strengthens neural pathways in your brain. You just got literally smarter.",
        "The way you broke down that problem was textbook, {name}.",
        "{name}, your growth in the last week has been remarkable. Keep this energy.",
        "Did you feel that click? That's what understanding feels like. Beautiful.",
        "You're not just answering correctly -- you're answering FASTER. That means real mastery.",
        "That was a tough one, and you handled it like a pro.",
        "I've seen a lot of players, {name}. Your progress curve is genuinely above average.",
        "Your brain is building connections right now that will serve you for years.",
        "Keep going like this and you'll unlock realms most players only dream about.",
        "You know what's special about you, {name}? You actually think before answering. That's rare.",
        "That {realm} challenge was meant for higher levels. You just punched above your weight.",
        "{name}, your consistency is your superpower. {streak} days of showing up -- that's character.",
        "You're starting to see patterns others miss. That's what {realm} mastery looks like.",
        "Another correct answer! You're on a roll, {name}.",
        "That was elegant. Not just correct -- elegant. There's a difference.",
        "Your problem-solving approach has matured so much. I can see the growth.",
        "Impressive time on that one! Speed AND accuracy -- that's the winning combo.",
        "You just solved something that stumps most players at your level. Remember this feeling.",
        "Level {level} earned, not given. You worked for every bit of this, {name}.",
        "{xp} XP is not a number -- it's proof of dedication.",
        "That one required both logic AND intuition. You used both perfectly.",
        "I notice you're trying different strategies now. That adaptability is a sign of intelligence.",
        "Your response time is dropping while your accuracy rises. That's the definition of improvement.",
        "Three in a row! Your confidence is well-earned, {name}.",
        "That challenge had a hidden trick in it. You caught it. Sharp.",
        "The fact that you even attempted that difficulty says something about your mindset.",
        "You're building mental muscle, {name}. Every rep counts, and this was a great one.",
        "Real progress isn't always visible day-to-day, but yours is. Genuinely.",
        "The way you handled that {realm} challenge -- you've clearly internalized the concepts.",
        "That's what mastery-in-progress looks like. You're getting there, {name}.",
        "Your best sessions always happen when you trust your instincts. Like right now.",
        # Personality-matched encouragement
        {'text': "That creative solution was unlike anything I've seen! You think differently, {name}, and that's a gift.", 'personality_match': {'openness': 65}},
        {'text': "Your methodical approach paid off perfectly. Discipline wins again, {name}.", 'personality_match': {'conscientiousness': 65}},
        {'text': "You should share that strategy with other players! They could learn from your approach.", 'personality_match': {'extraversion': 60}},
        {'text': "Quiet excellence, {name}. You don't need to be loud to be brilliant.", 'personality_match': {'extraversion': -65}},
        {'text': "I know you were worried about this one, but look -- you handled it perfectly.", 'personality_match': {'neuroticism': 60}},
        {'text': "See? When you trust the process, the results follow. Your patience is paying off.", 'personality_match': {'neuroticism': -60}},
        {'text': "Your approach helped everyone in that challenge. Leadership by example, {name}.", 'personality_match': {'agreeableness': 65}},
        {'text': "That competitive fire is serving you well, {name}. You're in it to win it.", 'personality_match': {'agreeableness': -60}},
        {'text': "Your analytical precision on that one was remarkable. You see the details others miss.", 'personality_match': {'analytical_thinking': 65}},
        {'text': "Risk-taking paid off there. Calculated boldness is a rare skill, {name}.", 'personality_match': {'risk_tolerance': 65}},
    ],

    # ================================================================== #
    # 3. CHALLENGE HELP (40 templates)
    # ================================================================== #
    'challenge_help': [
        "I won't give you the answer, but here's a nudge: look at it from a different angle.",
        "Think about what you already know about this topic, {name}. The answer builds on that.",
        "Here's a hint: try eliminating the options that definitely can't be right.",
        "What if you broke this into smaller pieces? Sometimes the whole is easier than it looks.",
        "Take a step back and re-read the question carefully. There might be a keyword you missed.",
        "This one is about {realm} principles. Which core concept applies here?",
        "I'll give you a hint without giving it away: the answer is simpler than you think.",
        "Try thinking about it from the opposite direction. If the answer were X, what would that imply?",
        "You've solved similar challenges before, {name}. What strategy worked then?",
        "Here's my approach: identify what you know for SURE, then work from there.",
        "Don't overthink it. Sometimes your first instinct in {realm} challenges is correct.",
        "Look for the pattern. {realm} challenges almost always have a pattern hidden in them.",
        "What's the relationship between the elements? That's usually the key to these.",
        "Three things to check: the context, the constraints, and the exceptions.",
        "If you were explaining this to someone, what would you say? Sometimes teaching reveals the answer.",
        "Focus on what makes this challenge DIFFERENT from the ones you've already solved.",
        "Hint: one of the options contradicts a basic {realm} principle. Can you spot which one?",
        "Take a breath and approach it fresh. Sometimes our first read creates a mental trap.",
        "I believe in your ability to figure this out, {name}. What's your gut telling you?",
        "There's a common misconception that trips people up here. Are you sure your assumption is right?",
        "This challenge tests a specific skill. What skill do you think it's testing?",
        "Look at the time limit -- it's generous for a reason. Use it to think through each option.",
        "In {realm}, the answer usually connects to the underlying principle, not surface details.",
        "What would happen if each option were true? Which one leads to a consistent outcome?",
        "Hint: draw it out mentally. Visualize the scenario described in the question.",
        "You've been getting harder challenges because you're improving. Trust your training, {name}.",
        "Before guessing, ask yourself: 'What is this question actually testing?'",
        "Sometimes the right answer is the one that feels least obvious at first.",
        "In {realm}, look for cause and effect. What causes what?",
        "The best players approach these by ruling out the wrong answers first. Try that.",
        "Here's a framework: consider it from psychological, logical, and practical perspectives.",
        "Think about real life. If this scenario actually happened, what would make sense?",
        "Careful with this one -- there might be more than one 'sort of right' answer. Find the BEST one.",
        "I can see you're close, {name}. Trust the reasoning process you've been building.",
        "This type of challenge has a common trap. The trap is assuming the obvious answer is correct.",
        "What information in the question can you use as a clue? Not all details are just decoration.",
        "Compare the options side by side. Which one addresses ALL parts of the question?",
        "Remember: in {realm}, context matters as much as content. What's the context here?",
        "You have the knowledge for this. The challenge is applying it correctly. Take your time.",
        "Sometimes the best hint is simply: read the question one more time, very carefully.",
    ],

    # ================================================================== #
    # 4. FRUSTRATION SUPPORT (50 templates)
    # ================================================================== #
    'frustration_support': [
        "I get it, {name}. This one is genuinely hard. But hard doesn't mean impossible.",
        "Feeling stuck is frustrating, I know. But it also means you're at the edge of growth.",
        "Take a deep breath, {name}. You don't have to solve everything right now.",
        "Every expert was once a beginner who felt exactly this frustrated. It passes.",
        "You know what? Let's take a different approach. Sometimes the path forward is sideways.",
        "It's okay to feel frustrated, {name}. That emotion means you care about doing well.",
        "Here's a secret: the challenges that frustrate you most are the ones that teach you most.",
        "Let's break this down together. What specifically is tripping you up?",
        "Sometimes the brain needs a reset. Want to try a different realm for a bit?",
        "You've overcome harder things than this, {name}. Check your achievement history -- it's proof.",
        "{name}, frustration is just your brain's way of saying 'I haven't figured this out YET.'",
        "The word 'yet' is the most powerful word in learning. You haven't mastered this YET.",
        "Want to hear something cool? Research shows that struggle improves long-term retention.",
        "Think about it: if this were easy, would you actually learn anything?",
        "Let's lower the stakes for a moment. This is a game. You're here to grow, not to be perfect.",
        "I'm not going anywhere, {name}. We'll figure this out together, at your pace.",
        "Your frustration is valid. And it will make the breakthrough feel even more satisfying.",
        "Sometimes the best move is to walk away, get a drink, and come back in 5 minutes.",
        "You're not failing, {name}. You're doing the hard work that most people avoid.",
        "The fact that you're still here, still trying? That's not failure -- that's grit.",
        "Even the best players have off days. What matters is showing up again tomorrow.",
        "Let me tell you what I see: someone who refuses to give up. That's incredibly valuable.",
        "Would it help to try an easier version of this concept first? No shame in building up.",
        "Your {streak}-day streak proves you're persistent. This challenge is temporary.",
        "I know it doesn't feel like it right now, but you're closer than you think.",
        "What if we approached this from a completely different direction?",
        "Remember: MindArena adjusts difficulty to keep you challenged. This means you've EARNED harder problems.",
        "The gap between where you are and where you want to be? That's called potential. You have loads of it.",
        "It's okay to ask for help, {name}. Smart people ask for help. It's literally a sign of intelligence.",
        "Let's celebrate the attempt. You're tackling something hard. That takes courage.",
        "Don't compare your chapter 1 to someone else's chapter 20. You're on your own timeline, {name}.",
        "Every wrong answer teaches your brain what NOT to do next time. That's useful data.",
        "Breathe. Reset. Try again. That's the cycle of mastery -- it's messy by design.",
        "You know what separates learners from quitters? Exactly this moment. And you're still here.",
        "I won't pretend this is easy. But I will remind you that you're tougher than you think.",
        "Would it help to talk through your thinking? Sometimes saying it out loud reveals the gap.",
        "Progress isn't always linear, {name}. There are dips before every climb.",
        "I've seen players at level {level} struggle with this exact thing. And then they broke through.",
        "Think of frustration as a signpost: 'Important learning ahead.' You're on the right path.",
        "Your feelings matter more than any score. Take a moment if you need one.",
        # Personality-matched frustration support
        {'text': "I know your analytical mind wants a clear path forward. Let me help you find one, step by step.", 'personality_match': {'analytical_thinking': 65}},
        {'text': "Your high standards are what make you good, {name}. But they can also make you hard on yourself. Ease up a little.", 'personality_match': {'conscientiousness': 70}},
        {'text': "Want to talk it out? Sometimes just expressing the frustration helps clear your thinking.", 'personality_match': {'extraversion': 60}},
        {'text': "It's okay to process this quietly, {name}. Take your time. I'll be here when you're ready.", 'personality_match': {'extraversion': -65}},
        {'text': "I notice you tend to worry when things get tough. Let me reassure you: this difficulty is DESIGNED. You're not failing.", 'personality_match': {'neuroticism': 65}},
        {'text': "Your emotional awareness is actually an asset here. You notice frustration early -- that means you can manage it.", 'personality_match': {'self_awareness': 60}},
        {'text': "Try using that creative problem-solving you're good at. Approach it like an artist, not a soldier.", 'personality_match': {'creative_thinking': 60}},
        {'text': "You're someone who helps others feel better. Now it's time to give that kindness to yourself, {name}.", 'personality_match': {'agreeableness': 65, 'empathy': 60}},
        {'text': "Channel that energy. Frustration and determination are the same fuel -- it depends on where you point it.", 'personality_match': {'risk_tolerance': 60}},
        {'text': "Trust the process, {name}. Your disciplined approach works -- it just needs a little more time here.", 'personality_match': {'conscientiousness': 60, 'neuroticism': -55}},
    ],

    # ================================================================== #
    # 5. FLOW STATE (30 templates)
    # ================================================================== #
    'flow_state': [
        "You're in the zone, {name}. I'll keep it quiet and let you work.",
        "Flow state detected. Keep that rhythm going -- everything is clicking.",
        "Your accuracy and speed are perfectly balanced right now. This is peak performance.",
        "You're on fire! I don't want to break your concentration, so I'll be brief: incredible work.",
        "The challenges are matching your skill level perfectly. That sweet spot is called flow.",
        "Don't stop now, {name}. You're in a state that athletes and musicians dream about.",
        "Your response times are beautifully consistent. That's the mark of flow.",
        "I'm watching excellence happen in real time. Keep going.",
        "Everything is aligned right now -- skill, challenge, focus. Ride this wave, {name}.",
        "This is what Csikszentmihalyi wrote about. You're experiencing optimal experience.",
        "You're answering like you can see the answers before reading the questions.",
        "Flow state: when skill meets challenge perfectly. You're there, {name}.",
        "Your brain is operating at peak efficiency right now. Let it run.",
        "I've tracked thousands of sessions. This is what an exceptional one looks like.",
        "Five in a row without hesitation. You're locked in, {name}.",
        "The way you're processing these challenges -- it's like watching a master at work.",
        "Keep this pace. You're building momentum that can carry through the entire session.",
        "Your focus right now is exactly what separates good players from the elite.",
        "I notice you're not even pausing to second-guess anymore. Pure confidence.",
        "This level of consistency is rare. You should feel proud of this session.",
        "Time probably feels different right now, right? That's flow -- time dissolves.",
        "You're making {realm} look easy. It isn't. You're just that good right now.",
        "Let me stay out of your way. When you're done, we'll celebrate.",
        "Each correct answer is fueling the next. Beautiful positive spiral, {name}.",
        "Your pattern recognition is operating at a different level today.",
        "I almost don't want to send this message and risk breaking your focus. You're that locked in.",
        "If you could bottle this mental state, it would be worth millions.",
        "The zone. The groove. The flow. Whatever you call it, you're in it.",
        "You're performing above your level average right now. The brain is a powerful thing in flow.",
        "Stay with it, {name}. Sessions like this are when the biggest leaps happen.",
    ],

    # ================================================================== #
    # 6. BOREDOM CHALLENGE (30 templates)
    # ================================================================== #
    'boredom_challenge': [
        "These are too easy for you, aren't they, {name}? Time to raise the bar.",
        "You look like you need a real challenge. Let's go up a difficulty level.",
        "Yawning yet? I've got something that'll wake you up. Ready for expert mode?",
        "{name}, your accuracy says you've outgrown this level. Let's fix that.",
        "Time for something new. Have you explored {realm} at higher difficulty?",
        "Easy is comfortable, but comfortable doesn't grow. Want me to push you?",
        "You're solving these in your sleep. Let's find your actual ceiling, {name}.",
        "I think you're ready for the arena. Want to test your skills against real players?",
        "Here's an idea: try a realm you haven't explored yet. Novelty wakes the brain up.",
        "What if we added a time constraint? Same challenges, but the clock is ticking.",
        "Have you tried the weekly quest in {realm}? It's designed for players at your skill level.",
        "Your brain is craving challenge and I can tell. Let me find something worthy.",
        "The side quests in {realm} have some genuinely tricky puzzles. Want to try one?",
        "You know what would be interesting? Try explaining your strategy to me. Teaching is harder than solving.",
        "Let's set a speed goal for the next five challenges. I bet you can shave off 20%.",
        "Boredom is actually a useful signal -- it means you need more complexity. Let's get you some.",
        "When was the last time a challenge made you really think? Let's find that level again.",
        "The creative challenges in the Creativity Nebula might surprise you, {name}.",
        "Pro move: try the same challenges without eliminating options first. Pure recall mode.",
        "What about competing for the weekly leaderboard? That adds a whole new dimension.",
        "Sometimes boredom means it's time for a new realm entirely. Which one intrigues you?",
        "I challenge you to a perfect session: 100% accuracy at the next difficulty tier. Dare?",
        "You've mastered the basics. Now let's see if you can handle the edge cases.",
        "The challenges get genuinely interesting at the next tier. Trust me on this, {name}.",
        "Your skills have outpaced the difficulty. That's a great problem to have.",
        "Let me throw some cross-realm challenges at you. They combine skills in unexpected ways.",
        "Ready for the speed run? Same challenge set, but racing against your personal best.",
        "The daily challenges update every day. Today's might actually test you.",
        "What if you tried {realm} challenges with the opposite approach to your usual strategy?",
        "Here's an unconventional suggestion: try the challenges you've been avoiding. They're usually the ones that teach the most.",
    ],

    # ================================================================== #
    # 7. GOAL SETTING (40 templates)
    # ================================================================== #
    'goal_setting': [
        "Let's set a goal for today, {name}. What would make you feel accomplished?",
        "Where do you want to be in one week? Let's reverse-engineer a plan to get there.",
        "Current level: {level}. What's your target level this month, {name}?",
        "Here's my suggestion: aim for 5 challenges per day in {realm}. That's sustainable growth.",
        "Your streak is {streak} days. Want to set a target for 30 days? You're closer than you think.",
        "What's the one skill you most want to improve? Let's make that our focus.",
        "Let's think big, {name}. If you could master any realm, which one would change your life most?",
        "Micro-goal for right now: complete the next 3 challenges with at least 80% accuracy. You in?",
        "Your {realm} level is {realm_level}. Getting to the next level unlocks new challenge types.",
        "I recommend setting both a daily goal and a weekly goal. Small wins fuel big progress.",
        "What's holding you back from the next level? Let's identify it and attack it.",
        "Smart goals are specific, {name}. Instead of 'get better at {realm}', try 'improve accuracy by 10%.'",
        "You've been focused on {realm}. Want to diversify? Exploring new realms gives compound benefits.",
        "Let's set a streak goal. {streak} is great -- what if we aimed for {streak} + 7?",
        "What about an XP goal? You're at {xp}. Reaching the next thousand would be a milestone.",
        "I can build you a weekly plan if you tell me: how many minutes per day can you commit?",
        "Your strongest realm is doing well. But your weakest realm is where the biggest growth opportunities are.",
        "Three paths forward: depth (master one realm), breadth (explore all), or challenge (push difficulty). Which appeals?",
        "Here's a pro tip: set goals based on PROCESS, not just results. 'Practice 15 minutes daily' beats 'get to level 10.'",
        "Want to try the '3-2-1' goal? 3 challenges in your strongest realm, 2 in your weakest, 1 in a new one.",
        "What's your dream achievement in MindArena? Let's work backwards from there.",
        "I notice you're strongest in {realm}. What if we leveraged that strength in the arena?",
        "Short-term goal: what can you achieve in the next 20 minutes of play?",
        "Mid-term goal: where do you want to be by the end of this week?",
        "Long-term goal: what kind of thinker do you want to become? Let's build toward that.",
        "Let's make your goal specific: 'I will complete [number] {realm} challenges at difficulty [X] this week.'",
        "Your current accuracy in {realm} is {accuracy}%. Want to target 5% improvement this week?",
        "The best players I've seen all had written goals. What's yours, {name}?",
        "Consider this: what would you attempt if you knew you couldn't fail?",
        "Let's set a 'reach' goal that excites you and a 'floor' goal you can definitely achieve.",
        "You're {xp} XP away from a major milestone. That's very achievable this week.",
        "Goal suggestion: try a new realm you haven't touched yet. Novelty boosts overall brain performance.",
        "What part of your real life would benefit most from MindArena training? Let's focus there.",
        "The arena rankings reset weekly. This could be your week to climb, {name}.",
        "I suggest tracking not just scores, but how you FEEL after each session. That's the deeper progress.",
        "Ready for a challenge? Try maintaining your streak for 21 days -- that's when habits solidify.",
        "Set a learning goal: 'By the end of this month, I want to understand [topic].' Then we'll build the path.",
        "Small consistent progress beats sporadic big efforts. What's a goal small enough to do EVERY day?",
        "Your goal should make you slightly nervous and slightly excited. That's the sweet spot.",
        "Let's review your goals from last session. Did you hit them? Either way, let's recalibrate.",
    ],

    # ================================================================== #
    # 8. SOCRATIC QUESTIONS (40 templates)
    # ================================================================== #
    'socratic_question': [
        "What evidence supports your answer? And what evidence contradicts it?",
        "If you had to argue the opposite position, what would you say?",
        "What assumptions are you making that might not be true?",
        "How would you explain your reasoning to someone who disagrees?",
        "What's the most important piece of information in this problem? Why?",
        "If the context were different, would your answer change? How?",
        "What's the difference between what you know and what you're guessing?",
        "Can you think of a real-world example that illustrates this concept?",
        "What would need to be true for the other option to be correct instead?",
        "Why do you think this question was asked in {realm} specifically?",
        "What's the underlying principle being tested here?",
        "If you came back to this challenge tomorrow, would you answer differently?",
        "What's the strongest argument against your chosen answer?",
        "How confident are you in your answer on a scale of 1-10? What would make it higher?",
        "Can you identify any logical fallacy in the incorrect options?",
        "What pattern connects this challenge to the previous ones you've solved?",
        "If you were designing this challenge, what would you make the 'trap' answer?",
        "What's the minimum information you need to solve this? Do you have it?",
        "How does this connect to what you already know about {realm}?",
        "If you explain your answer in one sentence, what would it be?",
        "What question would YOU ask to test understanding of this topic?",
        "What's the difference between getting this right by luck and getting it right by understanding?",
        "Can you trace your thinking step by step? Where does certainty end and guessing begin?",
        "What would a master of {realm} notice about this challenge that a beginner wouldn't?",
        "Is there a simpler way to think about this problem?",
        "What if I told you the most obvious answer is wrong? How would that change your approach?",
        "What does this challenge teach you about how {realm} works?",
        "If you got this wrong, what would the mistake teach you?",
        "What connections can you draw between this and challenges in OTHER realms?",
        "Are you solving this by recognizing a pattern, or by reasoning from first principles?",
        "What would you tell a friend who was stuck on this exact challenge?",
        "How many different ways could you approach this problem?",
        "What's the relationship between the question and the correct answer? Is it causal, correlational, or something else?",
        "If you remove one piece of information from the question, does the answer change?",
        "What mental model are you using to think about this? Is there a better one?",
        "Does your answer feel 'right' but you can't explain why? Let's dig into that.",
        "What's the cost of being wrong here? And what's the cost of not trying?",
        "Can you restate the problem in your own words? Sometimes rephrasing reveals the answer.",
        "What's the simplest version of this problem, and can you solve that first?",
        "If this were a conversation instead of a test, what would you want to discuss about it?",
    ],

    # ================================================================== #
    # 9. GROWTH MINDSET (40 templates)
    # ================================================================== #
    'growth_mindset': [
        "Mistakes aren't failures, {name} -- they're data points. And you just collected a valuable one.",
        "Carol Dweck says: 'The view you adopt for yourself profoundly affects the way you lead your life.'",
        "Your brain literally grows new connections when you struggle. You're building neural pathways right now.",
        "The word 'yet' changes everything. You haven't mastered this YET.",
        "'I can't do this' vs 'I can't do this yet.' One word. Infinite difference.",
        "Research shows that students who embrace mistakes learn faster. You're in good company, {name}.",
        "Talent is just a starting point. The players who grow the most are the ones who WORK the most.",
        "Every master was once a disaster. Every expert was once a beginner. You're on the path.",
        "Your intelligence isn't fixed, {name}. It's like a muscle -- it grows with exercise.",
        "The most successful people in history all had one thing in common: they failed more than average people even tried.",
        "Think of challenges as brain food, not brain tests. You're nourishing growth, not measuring worth.",
        "The discomfort you feel right now? Neuroscience calls that desirable difficulty. It means deep learning is happening.",
        "Edison didn't fail 1,000 times making the lightbulb. He found 1,000 ways that didn't work. Different mindset.",
        "Your effort matters more than your outcome. Process over results, {name}.",
        "When you say 'I'm not good at {realm},' add 'yet.' Then prove 'yet' wrong.",
        "Fixed mindset: 'I failed.' Growth mindset: 'I learned.' Which one moves you forward?",
        "Struggle is not a sign of weakness. It's a sign that you're attempting something meaningful.",
        "The gap between where you are and where you want to be? That's called potential, and you have plenty.",
        "Your brain doesn't know the difference between a 'failure' and a 'learning experience.' You decide the label.",
        "Players who believe they can improve -- actually improve faster. Belief shapes reality, {name}.",
        "Let me reframe that: you didn't get it wrong. You discovered a misconception to correct.",
        "Praising effort over talent leads to better outcomes. So: incredible effort on that one, {name}.",
        "When learning feels hard, that's literally your brain reorganizing itself. Trust the process.",
        "You're not competing against other players, {name}. You're competing against yesterday's version of yourself.",
        "Every wrong answer narrows down the possibilities. You're getting closer with each attempt.",
        "The best athletes in the world lose more than amateurs do. Because they compete more. Same principle here.",
        "Comfort means no growth. Discomfort means progress. You're progressing right now.",
        "If you want to be great at {realm}, you have to be willing to be bad at it first. And you're past that stage.",
        "A setback is a setup for a comeback. Classic growth mindset truth.",
        "Your willingness to try hard things says more about you than your accuracy score ever will.",
        "Neurons that fire together wire together. Every practice attempt is literally rewiring your brain.",
        "Don't judge yourself by today's performance. Judge yourself by today's effort.",
        "The most dangerous phrase in learning is 'I already know this.' Stay curious, stay growing, {name}.",
        "Failure is just success that hasn't happened yet. Keep going.",
        "Your potential isn't a ceiling -- it's a horizon. It moves forward as you do.",
        "Remember: the brain is plastic. It CHANGES based on what you do. You're shaping yours right now.",
        "What separates those who achieve from those who don't? It's not talent. It's persistence.",
        "You're in the 'messy middle' of learning. The part between beginning and mastery. This is where the magic happens.",
        "Challenge accepted is growth mindset. Challenge avoided is fixed mindset. You keep accepting. I notice that.",
        "Ten years from now, you'll be glad you pushed through this moment. Future-you is cheering for present-you.",
    ],

    # ================================================================== #
    # 10. MOTIVATIONAL (50 templates)
    # ================================================================== #
    'motivational': [
        "The only person you need to be better than is the person you were yesterday.",
        "Discipline is doing it when you don't feel like it. And you're here, {name}. That's discipline.",
        "Small steps every day lead to incredible results over time. Keep stepping.",
        "The difference between ordinary and extraordinary is that little 'extra'. You've got it, {name}.",
        "Winners are not people who never fail, but people who never quit.",
        "Your brain is the most powerful tool in the universe. Treat training it as the priority it is.",
        "Consistency beats intensity. Your {streak}-day streak proves you understand this.",
        "The fact that you're investing in your mind puts you ahead of 95% of people.",
        "Every minute you spend in MindArena is an investment that compounds over time.",
        "You don't have to be perfect. You just have to be better than you were.",
        "The best time to start was yesterday. The second best time is right now.",
        "Your future self will thank you for the effort you're putting in today, {name}.",
        "Success is rented, not owned. And the rent is due every day. You're paying it.",
        "The human brain has 86 billion neurons. You're training every one of them.",
        "Champions are made in the sessions nobody sees. This is one of those sessions.",
        "You showed up today. That's half the battle. Now let's win the other half.",
        "Mental fitness is just as important as physical fitness. You're training both.",
        "The compound effect: small daily improvements x 365 days = mind-blowing results.",
        "Every challenge you complete is a vote for the person you're becoming.",
        "Motivation gets you started. Discipline keeps you going. Habit makes it automatic. You're building habits.",
        "'Whether you think you can, or you think you can't -- you're right.' -- Henry Ford",
        "'The mind is everything. What you think you become.' -- Buddha",
        "'Education is not the filling of a pail, but the lighting of a fire.' -- Yeats",
        "'The unexamined life is not worth living.' -- Socrates. And you're examining yours.",
        "Did you know? Your brain uses 20% of your body's energy. You're literally burning calories right now, {name}.",
        "Fun fact: learning a new concept creates a physical change in your brain's structure.",
        "Psychological research shows that people who actively train their minds age more slowly. You're investing in longevity.",
        "Studies show that just 20 minutes of cognitive training per day measurably improves problem-solving ability.",
        "IQ isn't fixed. Fluid intelligence can be trained. That's exactly what you're doing right now.",
        "The 10,000-hour rule might be debated, but one thing is certain: deliberate practice works. This is deliberate practice.",
        "Emotional intelligence predicts success better than IQ. And {realm} challenges are building exactly that.",
        "Your brain's prefrontal cortex -- the decision-making center -- strengthens with every challenge you complete.",
        "History's greatest minds all had one thing in common: they never stopped learning.",
        "You're not just playing a game, {name}. You're building the mental architecture for your entire life.",
        "The average person spends 3 hours a day on social media. You're spending yours growing. Respect.",
        "In a world of distractions, choosing to train your mind is a radical act, {name}.",
        "Every realm you explore builds a different dimension of intelligence. You're becoming multidimensional.",
        "The Stoics believed that the mind is the only thing truly under your control. Train it accordingly.",
        "You know what separates high performers? They do the boring work when nobody's watching.",
        "Your potential is a function of effort multiplied by time. Keep investing both.",
        # Personality-matched motivational
        {'text': "Your curiosity is your compass, {name}. Follow it -- it's leading you somewhere extraordinary.", 'personality_match': {'openness': 65}},
        {'text': "Your structured approach is exactly what leads to mastery. Stay the course, {name}.", 'personality_match': {'conscientiousness': 65}},
        {'text': "Share your journey with others, {name}! Your progress might inspire someone who needs it.", 'personality_match': {'extraversion': 60}},
        {'text': "Quiet determination is an underrated superpower. And you have it in abundance, {name}.", 'personality_match': {'extraversion': -65}},
        {'text': "The world needs more people who care as deeply as you do. Keep going, {name}.", 'personality_match': {'agreeableness': 65}},
        {'text': "Your independence of thought is rare and valuable. Never stop questioning, {name}.", 'personality_match': {'agreeableness': -55, 'openness': 60}},
        {'text': "I know the pressure can feel heavy, but look how far you've come DESPITE it. That's strength, {name}.", 'personality_match': {'neuroticism': 65}},
        {'text': "Your emotional stability is an asset in {realm}. Calm minds solve the hardest problems.", 'personality_match': {'neuroticism': -60}},
        {'text': "Your creative eye sees solutions where others see walls. That's a rare gift, {name}.", 'personality_match': {'creative_thinking': 65}},
        {'text': "Your boldness in tackling hard challenges is exactly what separates good from great.", 'personality_match': {'risk_tolerance': 65}},
    ],

    # ================================================================== #
    # 11. REALM SPECIFIC (80 templates -- 10 per realm)
    # ================================================================== #
    'realm_specific': {
        # -------------------------------------------------------------- #
        # LOGIC FORTRESS
        # -------------------------------------------------------------- #
        'logic_fortress': [
            "In Logic Fortress, every problem has a structure. Find the structure, find the answer.",
            "Tip for logic challenges: try proof by contradiction. Assume the opposite and see if it breaks.",
            "The best logical thinkers don't just find the right answer -- they understand WHY every other answer is wrong.",
            "Logic Fortress is about building arguments that can't be knocked down. One premise at a time.",
            "Pattern recognition is the backbone of logical thinking. Look for what repeats, what changes, and what stays constant.",
            "In formal logic, the strength of a conclusion depends entirely on the strength of its premises. Check your foundations.",
            "Here's a Logic Fortress pro tip: draw it out. Diagrams make abstract logic tangible.",
            "Syllogisms, conditionals, and set theory -- these are the weapons of Logic Fortress. Sharpen them.",
            "The most common error in logic? Confusing correlation with causation. Watch for that trap.",
            "Logic is the foundation that every other realm builds upon. Mastering it pays compound interest.",
        ],
        # -------------------------------------------------------------- #
        # EMOTION OCEAN
        # -------------------------------------------------------------- #
        'emotion_ocean': [
            "Emotion Ocean teaches you to navigate feelings -- yours and others'. That's real intelligence.",
            "Tip: when reading emotional scenarios, pay attention to what's NOT said. Subtext matters.",
            "Emotional intelligence isn't about suppressing feelings. It's about understanding and channeling them.",
            "In Emotion Ocean, empathy is your compass. Try to feel what the characters in each scenario feel.",
            "The ability to name your emotions precisely is called emotional granularity. It's a trainable skill.",
            "Research shows that people with high EQ earn more, have better relationships, and live longer. This realm matters.",
            "When facing emotional scenarios, ask: 'What would I want someone to do for me in this situation?'",
            "Emotion Ocean challenges often test whether you can separate your reaction from the best response.",
            "The difference between sympathy and empathy: sympathy says 'I'm sorry.' Empathy says 'I understand.'",
            "Emotional regulation isn't about control -- it's about having a larger emotional vocabulary to choose from.",
        ],
        # -------------------------------------------------------------- #
        # CREATIVITY NEBULA
        # -------------------------------------------------------------- #
        'creativity_nebula': [
            "In the Creativity Nebula, there's no single right answer. There's an interesting answer waiting to be found.",
            "Creative thinking tip: combine two unrelated ideas. Innovation lives at the intersection.",
            "The best creative thinkers aren't the most talented -- they're the ones who generate the most ideas.",
            "Creativity isn't magic. It's a process: diverge widely, then converge on the best idea.",
            "In the Nebula, wrong answers are just unexplored possibilities. Treat them that way.",
            "Try the 'yes, and...' technique from improv. Build on ideas instead of judging them.",
            "Constraints actually boost creativity. The Nebula's rules aren't limitations -- they're launchpads.",
            "The most creative solutions often come from asking 'What if the opposite were true?'",
            "Creative blocks happen when you judge too early. Separate ideation from evaluation.",
            "Every innovation in history started with someone asking 'What if?' The Nebula rewards that question.",
        ],
        # -------------------------------------------------------------- #
        # DISCIPLINE CITADEL
        # -------------------------------------------------------------- #
        'discipline_citadel': [
            "The Discipline Citadel tests what matters most: can you do the right thing even when it's hard?",
            "Willpower is like a muscle -- it gets stronger with use and weaker without it. Train it here.",
            "Tip: discipline challenges often test delayed gratification. The best choice usually isn't the easy one.",
            "The Citadel teaches you that motivation is unreliable. Systems and habits are what actually work.",
            "Time management isn't about doing more. It's about doing what matters. The Citadel knows this.",
            "Every discipline challenge mirrors a real-life decision. Treat them with real-life seriousness.",
            "The gap between knowing and doing is what the Discipline Citadel bridges. It trains action, not just knowledge.",
            "Focus is the ability to say no to everything except the most important thing. The Citadel builds this.",
            "Consistency compound effect: 1% better every day = 37x better in a year. That's what discipline produces.",
            "The hardest challenges in the Citadel are the ones where the 'fun' option isn't the 'right' option. Choose wisely.",
        ],
        # -------------------------------------------------------------- #
        # KNOWLEDGE PEAKS
        # -------------------------------------------------------------- #
        'knowledge_peaks': [
            "Knowledge Peaks isn't about memorizing facts. It's about building frameworks for understanding.",
            "Tip: use spaced repetition. Reviewing old material at intervals beats cramming every time.",
            "The Peaks reward curiosity. The more connections you make between facts, the stronger your knowledge web.",
            "In Knowledge Peaks, context is everything. A fact without context is just trivia. With context, it's wisdom.",
            "The best learners don't just absorb information -- they actively question it. Be an active learner.",
            "Memory techniques: visualization, association, and chunking. Apply them in the Peaks.",
            "Knowledge Peaks challenges test both recall AND application. Knowing a fact isn't enough -- you need to USE it.",
            "The most effective study strategy: teach what you learn to someone else. Even imaginary audiences work.",
            "Here's a peak climbing tip: connect new knowledge to what you already know. Your brain stores information in networks.",
            "The difference between information and knowledge? Understanding. The Peaks build understanding, not just memory.",
        ],
        # -------------------------------------------------------------- #
        # SOCIAL BRIDGE
        # -------------------------------------------------------------- #
        'social_bridge': [
            "Social Bridge isn't about being popular. It's about understanding human dynamics and communicating effectively.",
            "Tip: in negotiation scenarios, focus on interests, not positions. What does each party actually need?",
            "The best communicators listen more than they speak. Social Bridge teaches this fundamental skill.",
            "Conflict resolution tip: seek to understand before being understood. The Bridge rewards this approach.",
            "Social intelligence is about reading the room, understanding subtext, and responding appropriately.",
            "In Social Bridge, the 'right' answer often depends on the relationship context. One size doesn't fit all.",
            "Persuasion without manipulation: that's the Social Bridge ideal. Influence through authenticity.",
            "Every conversation is a negotiation of some kind. The Bridge helps you navigate them with grace.",
            "Social scenarios have layers: what's said, what's meant, and what's needed. Look for all three.",
            "The Bridge connects all other realms. Logic, emotion, creativity, discipline -- they all need social skills to apply.",
        ],
        # -------------------------------------------------------------- #
        # WEALTH GARDEN
        # -------------------------------------------------------------- #
        'wealth_garden': [
            "The Wealth Garden isn't just about money. It's about understanding value, risk, and decision-making.",
            "Financial literacy tip: understand compound interest. Einstein called it the eighth wonder of the world.",
            "In the Garden, every decision has an opportunity cost. What are you giving up by choosing this option?",
            "The best financial decisions are often counterintuitive. The Garden trains you to see beyond the obvious.",
            "Behavioral economics shows that humans are predictably irrational with money. The Garden teaches rationality.",
            "Risk management isn't about avoiding risk -- it's about understanding and pricing it correctly.",
            "The Garden teaches you to think in systems. How does one financial decision cascade into others?",
            "Budgeting challenge tip: think in terms of trade-offs, not just limits. What's worth spending on?",
            "Wealth isn't just about earning more. It's about allocating wisely. The Garden teaches allocation.",
            "The most powerful financial concept: time value. A dollar today vs. a dollar tomorrow. The Garden explores this.",
        ],
        # -------------------------------------------------------------- #
        # WELLNESS GROVE
        # -------------------------------------------------------------- #
        'wellness_grove': [
            "The Wellness Grove reminds you: mental health is not a luxury, it's a foundation.",
            "Tip: mindfulness isn't about emptying your mind. It's about observing your thoughts without judgment.",
            "Stress management starts with awareness. The Grove trains you to notice stress before it becomes overwhelming.",
            "In the Grove, self-care isn't selfish -- it's strategic. You can't pour from an empty cup.",
            "Sleep, exercise, nutrition, and connection: the four pillars of wellness. The Grove covers them all.",
            "Wellness challenges test whether you can recognize healthy vs. unhealthy coping strategies.",
            "The Grove teaches you that prevention beats cure. Small daily practices prevent big breakdowns.",
            "Burnout doesn't happen overnight. It's the result of chronic neglect. The Grove builds awareness to prevent it.",
            "Resilience isn't about not falling. It's about getting back up. The Grove builds your bounce-back capacity.",
            "The Wellness Grove connects to every other realm. You can't think clearly, create freely, or lead effectively without wellness.",
        ],
    },

    # ================================================================== #
    # 12. STREAK MILESTONE (30 templates)
    # ================================================================== #
    'streak_milestone': [
        "1 day streak! Everyone starts somewhere. Welcome to the journey, {name}!",
        "3 days in a row! You're building a habit. That's how change starts.",
        "5-day streak! A full work week of mental training. That's real commitment, {name}.",
        "7-day streak! One full week. You've proven this isn't a passing interest.",
        "10-day streak! Double digits, {name}! You're in rare territory.",
        "14-day streak! Two weeks of daily practice. The habit is solidifying.",
        "21-day streak! They say it takes 21 days to form a habit. You just did it, {name}.",
        "30-day streak! A full month! Only 5% of players achieve this. You're elite.",
        "50-day streak! Halfway to 100. You're not just playing -- you're transforming, {name}.",
        "75-day streak! Three-quarters to a hundred. The dedication is extraordinary.",
        "100-day streak! TRIPLE DIGITS, {name}! This is genuinely impressive. Celebrate this.",
        "150-day streak! Over five months of daily practice. You're in the top 1% of all players.",
        "200-day streak! This level of consistency changes who you are as a person.",
        "365-day streak! ONE FULL YEAR, {name}! You've trained your mind every single day for a year. Legendary.",
        "{streak} days and counting! Every day you show up, you invest in your future self.",
        "Your {streak}-day streak puts you in the top tier of MindArena players. Well earned.",
        "Streak milestone: {streak} days! Consistency is the most underrated superpower.",
        "Day {streak} of your streak. Remember day 1? Look how far you've come.",
        "{streak} days of discipline. That's not motivation -- that's character, {name}.",
        "Your {streak}-day streak is proof that you take your growth seriously.",
        "Did you know? A {streak}-day streak means you've completed at least {streak} sessions. That's real investment.",
        "Streaks aren't about perfection, {name}. They're about showing up. And you keep showing up.",
        "{streak} days! Your brain has literally changed since day 1. New neural pathways, stronger connections.",
        "Your streak is {streak} days. That's {streak} days of choosing growth over comfort.",
        "If you play even one challenge per session, a {streak}-day streak means {streak}+ challenges completed. Incredible.",
        "Your streak journey: Day 1 was hope. Day {streak} is proof. Keep it going, {name}.",
        "{streak} consecutive days. That's not a number -- that's a statement about who you are.",
        "Every day of your {streak}-day streak, your brain got slightly better. The compound effect is real.",
        "You've logged in {streak} days straight. Most people can't stick with anything for {streak} days. You did.",
        "Streak milestone reached! {streak} days of intentional growth. Your future self is already thanking you.",
    ],

    # ================================================================== #
    # 13. LEVEL UP (20 templates)
    # ================================================================== #
    'level_up': [
        "LEVEL UP! Welcome to level {level}, {name}! New challenges await.",
        "You just hit level {level}! That's not just a number -- it's proof of growth.",
        "Level {level} unlocked! You've earned every bit of this, {name}.",
        "Congratulations, {name}! Level {level} brings harder challenges and bigger rewards.",
        "Level {level}! Remember when level 1 felt hard? Look at you now.",
        "You've leveled up to {level}! The view from up here is pretty good, isn't it?",
        "NEW LEVEL: {level}! Every level you gain represents real cognitive growth.",
        "Welcome to level {level}, {name}. The challenges here are tougher, but so are you.",
        "Level {level} achieved! You're in a club that most players only dream about joining.",
        "LEVEL {level}! Time to celebrate, then time to push even further.",
        "You've reached level {level}! Quick fact: only a fraction of players make it this far.",
        "Level up! {level} is your new normal. Let's see what you're capable of here.",
        "From 1 to {level} -- what a journey, {name}. Every challenge led to this moment.",
        "Level {level}! Your brain has literally reorganized itself to handle harder problems. Science is cool.",
        "Congrats on level {level}! New realms, new challenges, new opportunities to grow.",
        "You did it! Level {level}! Take a moment to feel proud -- then let's keep climbing.",
        "Level {level} -- a milestone worth remembering. Screenshot this moment, {name}!",
        "Each level represents hours of focused mental training. Level {level} is a real achievement.",
        "MILESTONE: Level {level}! Your dedication to growth is paying dividends, {name}.",
        "Level {level}! The higher you climb, the broader the view. What do you want to conquer next?",
    ],

    # ================================================================== #
    # 14. GENERAL / FALLBACK (30 templates)
    # ================================================================== #
    'general': [
        "I'm here for you, {name}. What can I help with?",
        "That's an interesting thought, {name}. Tell me more.",
        "Got it! Let me know how I can support you.",
        "I hear you, {name}. What would be most helpful right now?",
        "Thanks for sharing that. What would you like to work on?",
        "I'm listening, {name}. How can I help?",
        "Interesting perspective! Let's explore that further.",
        "That's a great question, {name}. Let's figure it out together.",
        "I appreciate you telling me that. Ready to jump into some challenges?",
        "Understood, {name}. Here's what I suggest: let's tackle what matters most to you right now.",
        "Every conversation teaches me more about how to help you, {name}.",
        "Good thought! The fact that you're thinking about this shows real self-awareness.",
        "Let me know what you need, {name}. I'm here to help you grow.",
        "That's a solid starting point. Let's build on it.",
        "Your mindset right now? Perfect for a productive session.",
        "Whatever you're working through, {name}, I'm on your team.",
        "I think the best thing we can do right now is jump into some challenges. What do you say?",
        "Noted! Now let's channel that energy into something productive.",
        "Every session starts with a conversation. And this one's off to a good start.",
        "You bring interesting thoughts every time, {name}. That's a sign of an active mind.",
        "I might be an AI companion, but I take your growth seriously, {name}.",
        "Whatever's on your mind, let's work through it -- one challenge at a time.",
        "The fact that you're here shows commitment. Let's make it count.",
        "Ready when you are, {name}. Today can be whatever you need it to be.",
        "I'm here to support YOUR journey, {name}. What direction do you want to go?",
        "Let's make this session count. What realm is calling your name today?",
        "One step at a time, {name}. That's how every great journey unfolds.",
        "I've got challenges, encouragement, and bad jokes. What would you like, {name}?",
        "Your mental health and growth matter to me. What can we work on?",
        "Whether you want to push hard or take it easy, I'm here for both. Your call, {name}.",
    ],
}


# ====================================================================== #
#                       TEMPLATE UTILITIES                                #
# ====================================================================== #

def get_template_count():
    """Return the total number of templates across all categories."""
    total = 0
    for key, val in TEMPLATES.items():
        if isinstance(val, list):
            total += len(val)
        elif isinstance(val, dict):
            for sub_list in val.values():
                if isinstance(sub_list, list):
                    total += len(sub_list)
    return total


def get_category_counts():
    """Return a dict of category -> template count."""
    counts = {}
    for key, val in TEMPLATES.items():
        if isinstance(val, list):
            counts[key] = len(val)
        elif isinstance(val, dict):
            counts[key] = sum(
                len(sub_list) for sub_list in val.values()
                if isinstance(sub_list, list)
            )
    return counts


def filter_by_personality(templates, personality):
    """Filter templates by personality match requirements.

    Parameters
    ----------
    templates : list
        List of template strings or dicts with ``text`` and ``personality_match``.
    personality : dict or None
        Player's personality traits. Keys are trait names, values are 0-100 scores.

    Returns
    -------
    list[str]
        Filtered templates as plain strings.
    """
    if not personality:
        # Return only simple string templates
        return [t if isinstance(t, str) else t['text'] for t in templates]

    result = []
    for template in templates:
        if isinstance(template, str):
            result.append(template)
            continue

        # Template is a dict with personality_match
        text = template.get('text', '')
        match_req = template.get('personality_match', {})
        matches = True

        for trait, threshold in match_req.items():
            player_val = personality.get(trait, 50)
            if threshold < 0:
                # Negative threshold: player must be LOW in this trait
                # e.g., threshold=-60 means player's trait must be < 40
                if player_val > (100 + threshold):
                    matches = False
                    break
            else:
                # Positive threshold: player must be HIGH in this trait
                if player_val < threshold:
                    matches = False
                    break

        if matches:
            result.append(text)

    return result


def fill_template(template, context):
    """Fill placeholders in a template string.

    Parameters
    ----------
    template : str
        Template with {placeholder} markers.
    context : dict
        Key-value pairs for placeholder substitution.

    Returns
    -------
    str
        Filled template string. Missing placeholders are left as-is.
    """
    try:
        # Use a safe substitution that won't raise on missing keys
        result = template
        for key, value in context.items():
            placeholder = '{' + str(key) + '}'
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result
    except Exception:
        return template


def get_realm_templates(realm_slug):
    """Get templates specific to a realm.

    Parameters
    ----------
    realm_slug : str
        The realm slug (e.g., 'logic_fortress', 'emotion_ocean').

    Returns
    -------
    list[str]
        Realm-specific templates, or general templates as fallback.
    """
    realm_templates = TEMPLATES.get('realm_specific', {})
    if isinstance(realm_templates, dict):
        return realm_templates.get(realm_slug, TEMPLATES.get('general', []))
    return TEMPLATES.get('general', [])
