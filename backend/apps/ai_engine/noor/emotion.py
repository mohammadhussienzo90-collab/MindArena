"""
Emotion Inference Engine
========================
Infer player emotional state from text messages and behavioral signals.

This module provides keyword-based text analysis and session-data behavioral
analysis to determine the player's current emotional state without requiring
any external API calls.

Emotional States
----------------
* **frustrated** -- repeated failure, negative language
* **anxious** -- worry, overwhelm, performance pressure
* **sad** -- loneliness, hopelessness, low energy
* **happy** -- positive language, excitement about progress
* **excited** -- anticipation, eagerness, high energy
* **bored** -- disengagement, lack of challenge
* **confused** -- lack of understanding, seeking help
* **proud** -- achievement, self-recognition
* **curious** -- exploration, questioning, wonder
* **flow** -- deep engagement (behavioral only)
* **engaged** -- steady improvement (behavioral only)
* **neutral** -- no strong signal detected

References
----------
- Ekman, P. (1992). An argument for basic emotions.
- Russell, J. A. (1980). A circumplex model of affect.
- Csikszentmihalyi, M. (1990). Flow: The Psychology of Optimal Experience.
"""


class EmotionEngine:
    """Infer player emotional state from text and behavior."""

    # ------------------------------------------------------------------ #
    # Emotion keyword patterns
    # ------------------------------------------------------------------ #
    EMOTION_KEYWORDS = {
        'frustrated': [
            'frustrated', 'stuck', 'cant', "can't", 'impossible',
            'give up', 'hate', 'stupid', 'useless', 'ugh', 'annoying',
            'fail', 'wrong again', 'not working', 'keeps failing',
            'no way', 'done with this', 'rage', 'so hard', 'too hard',
            'never get it', 'waste of time', 'this sucks', 'broken',
        ],
        'anxious': [
            'anxious', 'worried', 'nervous', 'scared', 'afraid',
            'stress', 'overwhelmed', 'panic', 'pressure', 'too much',
            'freaking out', 'cant handle', "can't handle", 'shaking',
            'heart racing', 'tense', 'dread', 'uneasy', 'on edge',
        ],
        'sad': [
            'sad', 'depressed', 'lonely', 'empty', 'hopeless',
            'worthless', 'crying', 'miss', 'lost', 'alone',
            'nobody cares', 'pointless', 'drained', 'tired of',
            'nothing matters', 'down', 'low', 'gutted',
        ],
        'happy': [
            'happy', 'great', 'awesome', 'amazing', 'love',
            'wonderful', 'fantastic', 'excellent', 'yes', 'yay',
            'woohoo', 'perfect', 'brilliant', 'best', 'incredible',
            'thank you', 'thanks', 'cool', 'nice', 'sweet',
        ],
        'excited': [
            'excited', 'cant wait', "can't wait", 'pumped', 'ready',
            'lets go', "let's go", 'bring it on', 'fire', 'hyped',
            'stoked', 'thrilled', 'buzzing', 'so ready', 'here we go',
            'amped', 'electrified', 'wired',
        ],
        'bored': [
            'bored', 'boring', 'meh', 'whatever', 'same',
            'repetitive', 'easy', 'too easy', 'nothing new',
            'not interesting', 'dull', 'lame', 'yawn', 'snooze',
            'so simple', 'already know', 'seen this before',
        ],
        'confused': [
            'confused', 'dont understand', "don't understand",
            'what is', 'what does', 'how does', 'how do i',
            'why does', 'why is', 'makes no sense', 'huh',
            'dont get it', "don't get it", 'explain', 'unclear',
            'which one', 'not sure', 'how does',
            'no idea', 'help me understand', 'i dont know',
        ],
        'proud': [
            'proud', 'did it', 'nailed', 'perfect', 'finally',
            'achievement', 'level up', 'streak', 'got it right',
            'crushed it', 'smashed it', 'on fire', 'unstoppable',
            'personal best', 'new record', 'mastered',
        ],
        'curious': [
            'curious', 'interesting', 'tell me', 'how does',
            'what if', 'wonder', 'explore', 'learn', 'fascinating',
            'want to know', 'teach me', 'show me', 'discover',
            'why does', 'explain more', 'deep dive', 'more about',
        ],
    }

    # Valence mapping for emotion intensity tracking
    EMOTION_VALENCE = {
        'frustrated': -0.7,
        'anxious': -0.5,
        'sad': -0.8,
        'happy': 0.8,
        'excited': 0.9,
        'bored': -0.3,
        'confused': -0.2,
        'proud': 0.9,
        'curious': 0.5,
        'flow': 0.7,
        'engaged': 0.5,
        'neutral': 0.0,
    }

    # Arousal mapping (energy level)
    EMOTION_AROUSAL = {
        'frustrated': 0.8,
        'anxious': 0.7,
        'sad': 0.2,
        'happy': 0.6,
        'excited': 0.9,
        'bored': 0.1,
        'confused': 0.4,
        'proud': 0.7,
        'curious': 0.6,
        'flow': 0.6,
        'engaged': 0.5,
        'neutral': 0.3,
    }

    # ------------------------------------------------------------------ #
    # Text-based inference
    # ------------------------------------------------------------------ #
    @classmethod
    def from_text(cls, message):
        """Infer emotion from message text.

        Parameters
        ----------
        message : str
            The player's message text.

        Returns
        -------
        tuple[str, float]
            (emotion_label, confidence) where confidence is 0.0--1.0.
        """
        if not message or not message.strip():
            return 'neutral', 0.3

        message_lower = message.lower().strip()

        # Check for question marks (boosts confused signal)
        question_count = message_lower.count('?')

        # Check for exclamation marks (boosts excited/frustrated signal)
        exclamation_count = message_lower.count('!')

        # Check for ALL CAPS words (emotional intensity)
        words = message.split()
        caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 1) / max(len(words), 1)

        scores = {}
        for emotion, keywords in cls.EMOTION_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in message_lower)
            if count > 0:
                scores[emotion] = count

        # Boost confused if lots of question marks
        if question_count >= 2:
            scores['confused'] = scores.get('confused', 0) + question_count * 0.5

        # Boost excited/frustrated with exclamation marks
        if exclamation_count >= 2:
            if 'frustrated' in scores:
                scores['frustrated'] += exclamation_count * 0.3
            if 'excited' in scores:
                scores['excited'] += exclamation_count * 0.3
            # CAPS + exclamation = intensity amplifier
            if caps_ratio > 0.3:
                for emo in scores:
                    scores[emo] *= 1.2

        # Short frustrated messages ("ugh", "stuck", "hate this")
        if len(words) <= 3 and 'frustrated' in scores:
            scores['frustrated'] *= 1.3

        if not scores:
            return 'neutral', 0.3

        best = max(scores, key=scores.get)
        # Confidence: 1 keyword = 0.33, 2 = 0.67, 3+ = 1.0
        confidence = min(1.0, scores[best] / 3.0)

        # Minimum confidence floor for detected emotions
        confidence = max(0.35, confidence)

        return best, round(confidence, 2)

    # ------------------------------------------------------------------ #
    # Behavior-based inference
    # ------------------------------------------------------------------ #
    @classmethod
    def from_behavior(cls, session_data):
        """Infer emotion from behavioral signals.

        Parameters
        ----------
        session_data : dict
            Must contain keys:
            - ``flow_score`` (float, 0-1)
            - ``accuracy`` (float, 0-1)
            - ``response_time_cv`` (float, coefficient of variation)
            - ``accuracy_trend`` (float, -1 to +1)

        Returns
        -------
        tuple[str, float]
            (emotion_label, confidence).
        """
        if not session_data:
            return 'neutral', 0.3

        flow = session_data.get('flow_score', 0)
        accuracy = session_data.get('accuracy', 0.5)
        cv = session_data.get('response_time_cv', 0.5)
        trend = session_data.get('accuracy_trend', 0)

        # Flow state: high flow score is the clearest behavioral signal
        if flow >= 0.7:
            return 'flow', round(0.6 + flow * 0.3, 2)

        # Boredom: very high accuracy + very consistent timing = understimulated
        if accuracy > 0.9 and cv < 0.3:
            confidence = 0.5 + (accuracy - 0.9) * 3 + (0.3 - cv)
            return 'bored', round(min(0.9, confidence), 2)

        # Frustration: low accuracy + erratic timing = struggling badly
        if accuracy < 0.3 and cv > 0.8:
            confidence = 0.5 + (0.3 - accuracy) + (cv - 0.8) * 0.5
            return 'frustrated', round(min(0.9, confidence), 2)

        # Anxiety: declining accuracy with moderate struggle
        if accuracy < 0.5 and trend < -0.2:
            confidence = 0.4 + abs(trend) + (0.5 - accuracy) * 0.5
            return 'anxious', round(min(0.85, confidence), 2)

        # Proud: high accuracy with improving trend
        if accuracy > 0.8 and trend > 0.1:
            return 'proud', round(0.5 + accuracy * 0.3, 2)

        # Engaged: positive trend, decent accuracy
        if trend > 0.15:
            confidence = 0.5 + trend
            return 'engaged', round(min(0.8, confidence), 2)

        # Confused: moderate accuracy but very erratic timing
        if 0.3 <= accuracy <= 0.6 and cv > 0.7:
            return 'confused', 0.5

        return 'neutral', 0.3

    # ------------------------------------------------------------------ #
    # Combined inference (text + behavior)
    # ------------------------------------------------------------------ #
    @classmethod
    def combined(cls, message, session_data=None):
        """Combine text and behavioral signals for best inference.

        Text analysis is primary when a message is provided. Behavioral
        data overrides only when its confidence exceeds the text signal.

        Parameters
        ----------
        message : str
            Player's text message.
        session_data : dict or None
            Behavioral metrics from the current session.

        Returns
        -------
        tuple[str, float]
            (emotion_label, confidence).
        """
        text_emotion, text_conf = cls.from_text(message)

        if session_data:
            behav_emotion, behav_conf = cls.from_behavior(session_data)

            # If both agree, boost confidence
            if text_emotion == behav_emotion:
                merged_conf = min(1.0, (text_conf + behav_conf) / 1.5)
                return text_emotion, round(merged_conf, 2)

            # If behavioral signal is stronger, prefer it
            if behav_conf > text_conf:
                return behav_emotion, behav_conf

        return text_emotion, text_conf

    # ------------------------------------------------------------------ #
    # Utility methods
    # ------------------------------------------------------------------ #
    @classmethod
    def get_valence(cls, emotion):
        """Get the valence (-1 negative to +1 positive) for an emotion."""
        return cls.EMOTION_VALENCE.get(emotion, 0.0)

    @classmethod
    def get_arousal(cls, emotion):
        """Get the arousal (0 calm to 1 activated) for an emotion."""
        return cls.EMOTION_AROUSAL.get(emotion, 0.3)

    @classmethod
    def is_negative(cls, emotion):
        """Return True if the emotion has negative valence."""
        return cls.get_valence(emotion) < -0.1

    @classmethod
    def is_high_energy(cls, emotion):
        """Return True if the emotion has high arousal."""
        return cls.get_arousal(emotion) > 0.6

    @classmethod
    def needs_support(cls, emotion):
        """Return True if the emotion warrants supportive intervention."""
        return emotion in ('frustrated', 'anxious', 'sad')

    @classmethod
    def suggest_action(cls, emotion, confidence):
        """Suggest a coaching action based on emotional state.

        Returns
        -------
        str
            One of: 'celebrate', 'support', 'challenge', 'guide',
            'motivate', 'maintain', 'default'.
        """
        if emotion in ('happy', 'proud', 'excited'):
            return 'celebrate'
        if emotion in ('frustrated', 'sad', 'anxious'):
            return 'support'
        if emotion == 'bored':
            return 'challenge'
        if emotion == 'confused':
            return 'guide'
        if emotion == 'flow':
            return 'maintain'
        if emotion == 'curious':
            return 'guide'
        if emotion == 'engaged':
            return 'motivate'
        return 'default'
