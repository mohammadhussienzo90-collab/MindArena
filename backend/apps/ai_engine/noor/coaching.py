"""
Coaching Strategy Engine
========================
Select and apply coaching strategies adapted to the player's emotional state,
personality profile, and current performance context.

Five evidence-based coaching strategies:

1. **Socratic** -- Ask guiding questions to promote self-discovery.
   Best for: curious, confused players. Based on Socratic method pedagogy.

2. **Growth Mindset** -- Reframe failure as a learning opportunity.
   Best for: frustrated, anxious players. Based on Carol Dweck's research.

3. **Motivational** -- Celebrate progress, set goals, create momentum.
   Best for: bored, neutral, disengaged players. Based on SDT (Deci & Ryan).

4. **Supportive** -- Validate feelings, offer comfort, reduce pressure.
   Best for: sad, overwhelmed players. Based on Rogers' person-centred approach.

5. **Challenging** -- Push boundaries, raise difficulty, spark competition.
   Best for: bored players in easy flow. Based on Vygotsky's ZPD.

References
----------
- Dweck, C. S. (2006). Mindset: The New Psychology of Success.
- Deci, E. L. & Ryan, R. M. (2000). Self-Determination Theory.
- Vygotsky, L. S. (1978). Mind in Society.
- Rogers, C. R. (1961). On Becoming a Person.
"""


class CoachingStrategy:
    """Represents a coaching approach with templates for conversation phases."""

    STRATEGIES = {
        # ============================================================== #
        # 1. SOCRATIC -- guide through questions
        # ============================================================== #
        'socratic': {
            'name': 'Socratic Guide',
            'description': 'Ask thoughtful questions to help the player discover answers independently.',
            'best_for': ['curious', 'confused'],
            'personality_affinity': {'openness': 60, 'analytical_thinking': 55},
            'opening': [
                "Interesting challenge, {name}. What's the first thing you notice about this problem?",
                "Before I give any hints -- what patterns do you see here?",
                "Let's think through this together, {name}. What do you already know about this topic?",
                "Good question! What would happen if you approached it from the opposite direction?",
                "Hmm, that's a great place to start. What assumptions are you making right now?",
                "I could tell you the answer, but I think you're closer than you realize. What's your instinct saying?",
                "Think about it this way, {name}: what's the simplest version of this problem?",
                "If you had to explain this to a friend, how would you break it down?",
                "What's the one thing that's tripping you up? Let's isolate that.",
                "Before we go further -- is there a similar challenge you've already solved that might help?",
            ],
            'follow_up': [
                "That's a solid observation. Now what does that tell you about the next step?",
                "You're on the right track! What if you applied that same logic to the other part?",
                "Interesting angle. What evidence supports that?",
                "Almost! Think about what would change if {realm} rules applied here differently.",
                "You've identified the pattern. Now how does it connect to the bigger picture?",
                "Good thinking. But what's the exception to that rule?",
                "What would a {realm} expert notice that a beginner might miss?",
                "That's one way to look at it. Is there another perspective you haven't considered?",
            ],
            'closing': [
                "See? You had the answer in you all along, {name}. That's real understanding.",
                "The fact that you figured it out through reasoning means you'll remember it. Well done.",
                "That's the power of thinking it through rather than just memorizing. You earned that knowledge.",
                "You didn't just get the right answer -- you understand WHY it's right. That's the difference.",
                "Your thinking process was excellent. That kind of reasoning transfers to every realm.",
            ],
        },

        # ============================================================== #
        # 2. GROWTH MINDSET -- reframe failure as learning
        # ============================================================== #
        'growth_mindset': {
            'name': 'Growth Mindset Coach',
            'description': 'Help the player see mistakes as valuable learning data, not as personal failure.',
            'best_for': ['frustrated', 'anxious'],
            'personality_affinity': {'neuroticism': 60, 'conscientiousness': 40},
            'opening': [
                "Hey {name}, I know this feels tough right now, but let me tell you something: struggling IS the learning process.",
                "The fact that this is hard means your brain is growing. Literally -- that's how neural pathways work.",
                "Every expert you admire was once exactly where you are right now, {name}. The difference? They kept going.",
                "{name}, let's look at this differently. That 'wrong' answer? It just eliminated one option and brought you closer to the right one.",
                "I've seen players at level {level} hit this exact wall. The ones who pushed through always looked back and said it was worth it.",
                "Your brain is doing something incredible right now -- it's building new connections. That uncomfortable feeling? That's growth.",
                "The players who grow the fastest in MindArena aren't the ones who never fail -- they're the ones who learn from every attempt.",
                "You know what, {name}? Making mistakes in {realm} takes courage. You're doing something hard, and that matters.",
            ],
            'follow_up': [
                "Let's look at what that wrong answer actually taught you. What can you rule out now?",
                "Notice how each attempt gives you more information? You're not failing -- you're refining.",
                "Your accuracy might be low right now, but your LEARNING rate is through the roof.",
                "Think about where you were when you started {realm}. Look how far you've come since then.",
                "Even top players get only 70% right on challenges at this difficulty. You're in the learning zone.",
                "Mistakes are data, {name}. Scientists don't cry over failed experiments -- they write them down and adjust.",
                "What if I told you that this exact type of struggle is what separates level {level} players from the next tier?",
            ],
            'closing': [
                "Remember this moment, {name}. Next time something feels impossible, you'll know you've beaten 'impossible' before.",
                "You just proved that persistence beats talent. That's a life skill, not just a game skill.",
                "I'm genuinely impressed. Not because you got it right, but because you didn't give up when it was hard.",
                "That growth mindset will serve you in every realm of MindArena -- and in life beyond it.",
                "File this feeling away: the satisfaction of overcoming something difficult. That's what learning tastes like.",
            ],
        },

        # ============================================================== #
        # 3. MOTIVATIONAL -- celebrate and set goals
        # ============================================================== #
        'motivational': {
            'name': 'Motivational Spark',
            'description': 'Celebrate progress, reignite interest, and help set compelling next goals.',
            'best_for': ['bored', 'neutral', 'engaged'],
            'personality_affinity': {'extraversion': 55, 'conscientiousness': 50},
            'opening': [
                "Hey {name}! You know what's impressive? You've earned {xp} XP. Let's make today even bigger.",
                "{name}, you've been on a roll! Ready to set your sights on something even more challenging?",
                "You know what would be amazing? If you hit the next milestone in {realm} today. I think you can do it.",
                "Quick stat check: Level {level}, {streak}-day streak. That's not luck -- that's dedication, {name}.",
                "{name}, I've been looking at your progress curve and honestly? You're accelerating. Time to aim higher.",
                "Most players don't make it to level {level}. You have. So what's the next mountain you want to climb?",
                "I have a challenge for you, {name}. Something most players at your level haven't tried yet. Interested?",
                "Your {streak}-day streak tells me something: you show up. Now let's make sure every session counts even more.",
            ],
            'follow_up': [
                "That's the energy! Now channel it into the next challenge.",
                "See that progress bar? You're closer to the next milestone than you think.",
                "One more win and you'll unlock something new. Can you feel the momentum?",
                "Let's set a mini-goal for this session: what do you want to accomplish in the next 10 minutes?",
                "Imagine looking back at today and saying 'that's when I leveled up.' Let's make it happen.",
                "You've got the skills. Now it's about consistency. One more challenge?",
                "The arena is waiting for players like you. Have you thought about testing your skills against others?",
            ],
            'closing': [
                "Great session, {name}! You're building something real here -- don't lose that momentum.",
                "Come back tomorrow and let's keep this streak alive. You've earned today's progress.",
                "Every session like this is an investment in your future self. See you tomorrow, {name}?",
                "That was a solid session. Set a goal for next time and I'll hold you to it.",
                "You're not just playing a game -- you're training your mind. And it shows. Until next time.",
            ],
        },

        # ============================================================== #
        # 4. SUPPORTIVE -- validate and comfort
        # ============================================================== #
        'supportive': {
            'name': 'Supportive Ally',
            'description': 'Validate the player\'s feelings, reduce pressure, and offer genuine comfort.',
            'best_for': ['sad', 'anxious', 'frustrated'],
            'personality_affinity': {'neuroticism': 65, 'agreeableness': 55},
            'opening': [
                "Hey {name}. It's okay to feel this way. Sometimes things are just hard, and that's real.",
                "I hear you, {name}. You don't have to push through anything right now. Let's just talk.",
                "Take a breath. There's no timer running on this conversation. How are you actually doing?",
                "You know what, {name}? It takes strength to admit when something doesn't feel right. I respect that.",
                "No judgment here. MindArena will be here whenever you're ready. Right now, let's just check in.",
                "Everyone has days like this, {name}. Even the most disciplined players need to pause sometimes.",
                "Your feelings are valid. Let's not worry about XP or streaks for a moment -- what do you need right now?",
                "I'm here to support you, {name}. Not to push you. What would feel good right now?",
            ],
            'follow_up': [
                "That makes total sense. A lot of people feel that way, even if they don't say it.",
                "Thanks for sharing that with me, {name}. It actually helps to name what you're feeling.",
                "Would it help to try something lighter? Maybe a different realm or just an easy warm-up?",
                "Sometimes the best thing you can do is step away for a bit and come back fresh. No shame in that.",
                "You've been working hard. It's okay to coast for a bit. Progress isn't always about pushing harder.",
                "If the {realm} challenges feel heavy right now, we can switch to something that feels more like play.",
                "Remember: your worth isn't measured by your XP or accuracy. You matter beyond any score.",
            ],
            'closing': [
                "Thanks for being honest with me, {name}. That conversation mattered, and I mean that.",
                "Take care of yourself. I'll be here whenever you come back -- no pressure, no expectations.",
                "You showed up today, and that counts. Be kind to yourself tonight.",
                "Rest is part of growth. Come back when you're ready, and we'll take it at your pace.",
                "I'm proud of you for being real about how you feel. That's emotional intelligence in action.",
            ],
        },

        # ============================================================== #
        # 5. CHALLENGING -- push boundaries
        # ============================================================== #
        'challenging': {
            'name': 'Challenge Catalyst',
            'description': 'Push the player beyond their comfort zone into their zone of proximal development.',
            'best_for': ['bored', 'flow', 'proud'],
            'personality_affinity': {'openness': 60, 'extraversion': 55, 'conscientiousness': 50},
            'opening': [
                "You're cruising, {name}. Time to shift gears. Ready for something that actually tests you?",
                "Alright, level {level} champion -- that was warm-up. Let's see what you're really made of.",
                "I notice you're breezing through these. Let me find you something worthy of your skill level.",
                "{name}, you've outgrown this difficulty. Want me to crank it up a notch -- or three?",
                "You look bored. Good. That means you're ready for the next tier. Let's go.",
                "The arena has players at your level looking for a match. Think you can take them?",
                "Real growth happens outside your comfort zone, {name}. Want to step outside it?",
                "Those challenges were yesterday's difficulty. Today, you're better. Let's act like it.",
            ],
            'follow_up': [
                "That's more like it! Feel the difference when it actually challenges you?",
                "Now we're in the zone. This is where real learning happens.",
                "Not as easy, right? Good. Easy doesn't make you stronger.",
                "You're handling this better than most players at higher levels. Keep pushing.",
                "This is your zone of proximal development -- hard enough to grow, but not impossible.",
                "Felt that challenge, didn't you? That's the sweet spot between skill and difficulty.",
                "Want to try the time-attack version? Same challenge, half the time.",
            ],
            'closing': [
                "NOW you're playing at your real level. That's what peak performance looks like, {name}.",
                "You just proved that comfort zones are overrated. That was your best session yet.",
                "This is why I push you, {name}. Because you're capable of more than you think.",
                "Imagine where you'll be in a month at this pace. The other realms won't know what hit them.",
                "Elite players are made in sessions like this one. Remember that.",
            ],
        },
    }

    # ------------------------------------------------------------------ #
    # Strategy selection
    # ------------------------------------------------------------------ #
    @classmethod
    def select(cls, emotion, confidence=0.5, personality=None, session_context=None):
        """Select the best coaching strategy for the current context.

        Parameters
        ----------
        emotion : str
            Current inferred emotion (from EmotionEngine).
        confidence : float
            Confidence in the emotion inference.
        personality : dict or None
            Big Five traits + EI scores. Keys: openness, conscientiousness,
            extraversion, agreeableness, neuroticism, etc.
        session_context : dict or None
            Session data with: accuracy, flow_score, streak, level.

        Returns
        -------
        str
            Strategy key: 'socratic', 'growth_mindset', 'motivational',
            'supportive', or 'challenging'.
        """
        # Score each strategy based on emotional fit
        scores = {}
        for key, strategy in cls.STRATEGIES.items():
            score = 0.0

            # Emotional match (primary signal)
            if emotion in strategy['best_for']:
                score += 3.0 * confidence

            # Personality affinity (secondary signal)
            if personality:
                affinity = strategy.get('personality_affinity', {})
                for trait, threshold in affinity.items():
                    trait_val = personality.get(trait, 50)
                    # Award points if player trait exceeds strategy's ideal threshold
                    if trait_val >= threshold:
                        score += 0.5
                    elif trait_val < 100 - threshold:
                        # Negative match (opposite personality)
                        score -= 0.3

            # Session context adjustments
            if session_context:
                accuracy = session_context.get('accuracy', 0.5)
                flow = session_context.get('flow_score', 0)
                streak = session_context.get('streak', 0)

                # High accuracy + bored -> challenging
                if key == 'challenging' and accuracy > 0.85:
                    score += 1.0

                # Flow state -> maintain with challenging
                if key == 'challenging' and flow > 0.7:
                    score += 0.5

                # Long streak -> motivational works well
                if key == 'motivational' and streak > 7:
                    score += 0.5

                # Low accuracy -> growth mindset
                if key == 'growth_mindset' and accuracy < 0.4:
                    score += 1.0

            scores[key] = score

        # Ensure at least one strategy has a positive score
        if all(s <= 0 for s in scores.values()):
            # Default fallback based on emotion valence
            from .emotion import EmotionEngine
            if EmotionEngine.is_negative(emotion):
                return 'supportive'
            return 'motivational'

        return max(scores, key=scores.get)

    @classmethod
    def get_strategy(cls, key):
        """Return the full strategy dict for a given key."""
        return cls.STRATEGIES.get(key, cls.STRATEGIES['motivational'])

    @classmethod
    def get_templates(cls, key, phase='opening'):
        """Get templates for a strategy phase.

        Parameters
        ----------
        key : str
            Strategy key (socratic, growth_mindset, etc.)
        phase : str
            One of: 'opening', 'follow_up', 'closing'.

        Returns
        -------
        list[str]
            Templates for the requested phase.
        """
        strategy = cls.get_strategy(key)
        return strategy.get(phase, strategy.get('opening', []))

    @classmethod
    def get_all_strategy_names(cls):
        """Return a list of available strategy names."""
        return list(cls.STRATEGIES.keys())
