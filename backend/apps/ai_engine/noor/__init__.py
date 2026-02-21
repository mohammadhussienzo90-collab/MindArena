"""
Smart Noor -- Offline AI Companion for MindArena
=================================================
Template-based, psychologically informed AI companion that operates
entirely without external API calls.

Modules
-------
- ``emotion`` -- Emotion inference from text and behavior
- ``coaching`` -- Adaptive coaching strategy selection
- ``templates`` -- 500+ response templates with personality matching
- ``engine`` -- Main orchestration engine

Quick Start
-----------
::

    from apps.ai_engine.noor import SmartNoorEngine

    # Full response with player context
    result = SmartNoorEngine.generate_response(player, "I'm stuck!")

    # Quick response without Django models
    text = SmartNoorEngine.quick_response("Ahmed", "Hello!")
"""

from .engine import SmartNoorEngine  # noqa: F401

__all__ = ['SmartNoorEngine']
