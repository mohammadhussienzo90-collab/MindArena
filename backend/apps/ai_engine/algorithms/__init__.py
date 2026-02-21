"""
AI Engine Algorithms
====================
Core algorithmic components for MindArena's adaptive learning system.

Modules
-------
irt          : Item Response Theory (2PL/3PL) for ability estimation
fsrs         : Free Spaced Repetition Scheduler (FSRS-4.5)
bkt          : Bayesian Knowledge Tracing
behavior     : Player behavior analytics (flow, emotion, engagement, churn)
recommender  : Hybrid 6-signal recommendation engine
learning_path: Skill prerequisite graph and curriculum optimizer
glicko2      : Glicko-2 competitive rating system
"""
from .behavior import BehaviorEngine
from .bkt import BKTEngine
from .fsrs import FSRSEngine
from .glicko2 import (
    match_quality,
    process_arena_match,
    update_rating,
)
from .irt import IRTEngine
from .learning_path import (
    SKILL_GRAPH,
    generate_learning_path,
    generate_weekly_plan,
    topological_sort,
)
from .recommender import (
    collaborative_score,
    content_based_score,
    hybrid_recommend,
    thompson_sampling,
)

__all__ = [
    'BehaviorEngine',
    'BKTEngine',
    'FSRSEngine',
    'IRTEngine',
    'SKILL_GRAPH',
    'collaborative_score',
    'content_based_score',
    'generate_learning_path',
    'generate_weekly_plan',
    'hybrid_recommend',
    'match_quality',
    'process_arena_match',
    'thompson_sampling',
    'topological_sort',
    'update_rating',
]
