"""Challenge validation and quest completion logic."""


def validate_challenge_answer(challenge, answer_data, time_taken_secs):
    """Validate a player's answer to a challenge. Returns result dict."""
    content = challenge.content
    challenge_type = challenge.challenge_type
    score = 0
    is_correct = False
    explanation = content.get('explanation_en', '')

    if challenge_type in ('multiple_choice', 'pattern_match', 'math_logic', 'sequence'):
        correct_index = content.get('correct_index')
        player_answer = answer_data.get('selected_index')
        is_correct = player_answer == correct_index
        score = 100 if is_correct else 0

    elif challenge_type == 'scenario_choice':
        selected = answer_data.get('selected_index', 0)
        choices = content.get('choices', [])
        if 0 <= selected < len(choices):
            choice_scores = choices[selected].get('scores', {})
            max_possible = max(
                sum(c.get('scores', {}).values()) for c in choices
            ) if choices else 1
            actual = sum(choice_scores.values())
            score = int((actual / max_possible) * 100) if max_possible > 0 else 50
            is_correct = score >= 70

    elif challenge_type == 'timed_response':
        is_correct = answer_data.get('correct', False)
        time_limit = challenge.time_limit_secs or 30
        if is_correct:
            speed_bonus = max(0, 1 - (time_taken_secs / time_limit))
            score = int(70 + speed_bonus * 30)
        else:
            score = 0

    elif challenge_type in ('creative_prompt', 'emotional_scenario'):
        # These are evaluated by AI companion in a separate step
        # For now, give base score for completion
        score = 70
        is_correct = True

    else:
        is_correct = answer_data.get('correct', False)
        score = 100 if is_correct else 0

    # Calculate bonus (perfect score + fast completion)
    bonus = False
    if score == 100 and challenge.time_limit_secs:
        if time_taken_secs < challenge.time_limit_secs * 0.5:
            bonus = True

    return {
        'score': score,
        'is_correct': is_correct,
        'explanation': explanation,
        'base_xp': challenge.base_xp if is_correct else int(challenge.base_xp * 0.2),
        'bonus_xp': challenge.bonus_xp if bonus else 0,
        'bonus': bonus,
        'trait_points': challenge.trait_points if is_correct else {},
    }
