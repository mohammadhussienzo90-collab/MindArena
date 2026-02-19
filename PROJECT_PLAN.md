# MindArena — Complete Project Plan (Part 2)

## Table of Contents
1. [Technology Stack](#1-technology-stack)
2. [Project Architecture](#2-project-architecture)
3. [Database Schema](#3-database-schema)
4. [Django Backend Structure](#4-django-backend-structure)
5. [API Endpoints](#5-api-endpoints)
6. [Godot Game Client Structure](#6-godot-game-client-structure)
7. [Personality Assessment System](#7-personality-assessment-system)
8. [Challenge & Quest System](#8-challenge--quest-system)
9. [Progression & XP System](#9-progression--xp-system)
10. [AI Companion Architecture](#10-ai-companion-architecture)
11. [Feed System](#11-feed-system)
12. [Visual Design & 3D World](#12-visual-design--3d-world)
13. [Realm Designs](#13-realm-designs)
14. [Character System](#14-character-system)
15. [Audio & Music](#15-audio--music)
16. [Localization (EN/AR)](#16-localization-enar)
17. [Security & Anti-Cheat](#17-security--anti-cheat)
18. [Monetization Implementation](#18-monetization-implementation)
19. [Development Schedule (2-Week MVP)](#19-development-schedule-2-week-mvp)
20. [Post-MVP Roadmap](#20-post-mvp-roadmap)
21. [Questions for Review](#21-questions-for-review)

---

## 1. Technology Stack

### Game Client (Godot)
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Game Engine | Godot Engine | 4.3+ | 3D world, gameplay, rendering |
| Scripting | GDScript | 2.0 | Game logic (Python-like syntax) |
| 3D Format | glTF 2.0 (.glb) | - | 3D model import format |
| Physics | Godot Physics | Built-in | Character controller, collisions |
| UI | Godot Control nodes | Built-in | HUD, menus, chat, feed |
| Audio | Godot AudioServer | Built-in | Music, SFX, ambient sounds |
| Networking | HTTPRequest node | Built-in | REST API calls to Django |
| Web Export | Godot HTML5 | Built-in | WebGL/WebAssembly browser build |
| Android Export | Godot Android | Built-in | APK/AAB builds |

### Backend (Django)
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Django | 5.1+ | Web framework, ORM |
| API | Django REST Framework | 3.15+ | REST API endpoints |
| Auth | djangorestframework-simplejwt | 5.3+ | JWT token authentication |
| Database | PostgreSQL | 16+ | Primary database |
| Cache | Redis | 7+ | Caching, session store, leaderboards |
| Task Queue | Celery | 5.4+ | Background tasks (AI, stats recalc) |
| AI | anthropic (Python SDK) | latest | Claude API for AI companion |
| CORS | django-cors-headers | 4.3+ | Cross-origin for game client |
| Storage | Django Storages + S3 | - | Static/media file hosting |
| Deploy | Railway | - | Hosting (PostgreSQL + Redis + Web) |
| Monitoring | Sentry | latest | Error tracking |

### Development Tools
| Tool | Purpose |
|------|---------|
| Git + GitHub | Version control |
| VS Code | Django development |
| Godot Editor | Game development |
| Blender 4.0+ | 3D modeling (if custom assets needed) |
| Figma | UI/UX mockups |
| Postman | API testing |

### Required Installations (Day 0 Setup)
```
1. Godot Engine 4.3 (download from godotengine.org)
2. Python 3.12+
3. PostgreSQL 16
4. Redis (via Docker or native)
5. Node.js (for any build tooling)
6. Blender 4.0 (optional, for custom 3D assets)
7. Android SDK (for mobile export, can defer)
```

---

## 2. Project Architecture

```
┌──────────────────────────────────────────────────────┐
│                    PLAYER DEVICE                      │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │            GODOT GAME CLIENT                    │  │
│  │                                                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────┐  │  │
│  │  │ 3D World │ │  Feed    │ │ AI Companion  │  │  │
│  │  │ Explorer │ │  Scroller│ │ Chat UI       │  │  │
│  │  └────┬─────┘ └────┬─────┘ └──────┬────────┘  │  │
│  │       │             │              │            │  │
│  │  ┌────┴─────────────┴──────────────┴────────┐  │  │
│  │  │         API SERVICE LAYER                 │  │  │
│  │  │  (HTTPRequest → JSON → Django REST API)   │  │  │
│  │  └──────────────────┬────────────────────────┘  │  │
│  └─────────────────────┼───────────────────────────┘  │
└────────────────────────┼──────────────────────────────┘
                         │ HTTPS (JWT Auth)
                         ▼
┌──────────────────────────────────────────────────────┐
│                DJANGO BACKEND (Railway)               │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Auth API │ │ Game API │ │ AI API   │ │Feed API│ │
│  │ /api/auth│ │/api/game │ │/api/ai   │ │/api/feed│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │
│       │             │            │            │      │
│  ┌────┴─────────────┴────────────┴────────────┴──┐  │
│  │              DJANGO ORM / SERVICES             │  │
│  └───────┬──────────────┬────────────────┬───────┘  │
│          │              │                │           │
│  ┌───────▼──────┐ ┌────▼─────┐  ┌──────▼────────┐ │
│  │ PostgreSQL   │ │  Redis    │  │  Claude API   │ │
│  │ (all data)   │ │ (cache,   │  │  (AI comp.)   │ │
│  │              │ │ leaders)  │  │               │ │
│  └──────────────┘ └──────────┘  └───────────────┘ │
└──────────────────────────────────────────────────────┘
```

### Communication Flow
1. Godot client authenticates → gets JWT tokens
2. All API calls include `Authorization: Bearer <access_token>`
3. Game state saved to server after each challenge completion
4. AI companion messages sent to Django → forwarded to Claude API → response returned
5. Feed content fetched in paginated batches
6. Leaderboard reads from Redis sorted sets (fast)
7. Stat recalculation happens via Celery background tasks

---

## 3. Database Schema

### Entity Relationship Overview
```
Player ──1:1── PlayerProfile ──1:1── PersonalityAssessment
   │                │
   │                ├──1:N── PlayerRealmStat (8 realms)
   │                ├──1:N── PlayerAchievement
   │                ├──1:N── XPTransaction
   │                └──1:N── PlayerQuestProgress
   │
   ├──1:N── CompanionConversation ──1:N── CompanionMessage
   ├──1:N── FeedInteraction
   ├──1:N── ArenaMatch
   └──1:N── DailyStreak

Realm ──1:N── Quest ──1:N── Challenge
                              │
                              ├──1:N── ChallengeOption (for MCQ)
                              └──1:N── ChallengeHint

FeedItem ──1:N── FeedInteraction
Achievement (static catalog)
```

### Complete Table Definitions

#### `players` (extends Django User)
```sql
CREATE TABLE players (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT UNIQUE REFERENCES auth_user(id),
    display_name    VARCHAR(50) NOT NULL,
    avatar_preset   VARCHAR(30) DEFAULT 'default',
    avatar_colors   JSONB DEFAULT '{}',           -- skin, hair, outfit color codes
    overall_level   INTEGER DEFAULT 1,
    total_xp        BIGINT DEFAULT 0,
    premium_tier    VARCHAR(20) DEFAULT 'free',    -- free, premium
    preferred_lang  VARCHAR(5) DEFAULT 'en',       -- en, ar
    timezone        VARCHAR(50) DEFAULT 'UTC',
    onboarding_done BOOLEAN DEFAULT FALSE,
    last_active_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_players_level ON players(overall_level DESC);
CREATE INDEX idx_players_xp ON players(total_xp DESC);
```

#### `personality_assessments`
```sql
CREATE TABLE personality_assessments (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    assessment_type VARCHAR(20) NOT NULL,          -- 'initial', 'periodic', 'detailed'

    -- Big Five (OCEAN) scores: 0-100
    openness            SMALLINT CHECK (openness BETWEEN 0 AND 100),
    conscientiousness    SMALLINT CHECK (conscientiousness BETWEEN 0 AND 100),
    extraversion         SMALLINT CHECK (extraversion BETWEEN 0 AND 100),
    agreeableness        SMALLINT CHECK (agreeableness BETWEEN 0 AND 100),
    neuroticism          SMALLINT CHECK (neuroticism BETWEEN 0 AND 100),

    -- EQ components: 0-100
    self_awareness       SMALLINT CHECK (self_awareness BETWEEN 0 AND 100),
    self_regulation      SMALLINT CHECK (self_regulation BETWEEN 0 AND 100),
    motivation           SMALLINT CHECK (motivation BETWEEN 0 AND 100),
    empathy              SMALLINT CHECK (empathy BETWEEN 0 AND 100),
    social_skills        SMALLINT CHECK (social_skills BETWEEN 0 AND 100),

    -- Cognitive baseline: 0-100
    logical_reasoning    SMALLINT CHECK (logical_reasoning BETWEEN 0 AND 100),
    creative_thinking    SMALLINT CHECK (creative_thinking BETWEEN 0 AND 100),
    processing_speed     SMALLINT CHECK (processing_speed BETWEEN 0 AND 100),
    working_memory       SMALLINT CHECK (working_memory BETWEEN 0 AND 100),

    -- Raw answers stored for re-analysis
    raw_answers     JSONB DEFAULT '{}',

    completed_at    TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_assess_player ON personality_assessments(player_id, completed_at DESC);
```

#### `realms`
```sql
CREATE TABLE realms (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(50) UNIQUE NOT NULL,   -- 'logic_fortress', 'emotion_ocean', etc.
    name_en         VARCHAR(100) NOT NULL,
    name_ar         VARCHAR(100),
    description_en  TEXT,
    description_ar  TEXT,
    icon            VARCHAR(50),                   -- icon identifier
    color_primary   VARCHAR(7),                    -- hex color
    color_secondary VARCHAR(7),
    unlock_level    INTEGER DEFAULT 1,             -- player level needed to access
    sort_order      SMALLINT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,

    -- Which personality/cognitive traits this realm maps to
    primary_trait   VARCHAR(30),                   -- e.g., 'logical_reasoning'
    secondary_trait VARCHAR(30),                   -- e.g., 'processing_speed'

    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `quests`
```sql
CREATE TABLE quests (
    id              BIGSERIAL PRIMARY KEY,
    realm_id        INTEGER REFERENCES realms(id),
    slug            VARCHAR(100) UNIQUE NOT NULL,
    title_en        VARCHAR(200) NOT NULL,
    title_ar        VARCHAR(200),
    description_en  TEXT,
    description_ar  TEXT,
    quest_type      VARCHAR(30) NOT NULL,          -- 'main', 'side', 'daily', 'weekly'

    -- Ordering and prerequisites
    sort_order      INTEGER DEFAULT 0,
    prerequisite_quest_id BIGINT REFERENCES quests(id),
    required_realm_level  INTEGER DEFAULT 0,

    -- Rewards
    xp_reward       INTEGER DEFAULT 0,
    stat_reward     JSONB DEFAULT '{}',            -- {"logical_reasoning": 2, "processing_speed": 1}
    achievement_id  INTEGER,                       -- unlocks achievement on completion

    -- Narrative
    intro_dialogue  JSONB DEFAULT '[]',            -- AI companion dialogue before quest
    outro_dialogue  JSONB DEFAULT '[]',            -- AI companion dialogue after quest

    -- 3D world
    world_position  JSONB DEFAULT '{}',            -- {"x": 10.5, "y": 0, "z": -5.2}
    world_marker    VARCHAR(50),                   -- visual marker type in 3D world

    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_quests_realm ON quests(realm_id, sort_order);
```

#### `challenges`
```sql
CREATE TABLE challenges (
    id              BIGSERIAL PRIMARY KEY,
    quest_id        BIGINT REFERENCES quests(id),
    slug            VARCHAR(100) UNIQUE NOT NULL,

    -- Challenge definition
    challenge_type  VARCHAR(30) NOT NULL,
    -- Types: 'multiple_choice', 'sequence', 'spatial_puzzle', 'timed_response',
    --        'scenario_choice', 'pattern_match', 'word_puzzle', 'math_logic',
    --        'emotional_scenario', 'creative_prompt', 'memory_test',
    --        'debate_analysis', 'financial_decision', 'stress_scenario'

    title_en        VARCHAR(200) NOT NULL,
    title_ar        VARCHAR(200),
    description_en  TEXT,
    description_ar  TEXT,

    -- Content (flexible JSON for different challenge types)
    content         JSONB NOT NULL,
    -- Example for multiple_choice:
    -- {"question": "...", "options": [...], "correct": 0, "explanation": "..."}
    -- Example for scenario_choice:
    -- {"scenario": "...", "choices": [{"text":"...", "scores":{"empathy":3,"self_reg":1}}]}
    -- Example for spatial_puzzle:
    -- {"puzzle_scene": "logic_01", "solution": [...], "time_limit": 60}
    -- Example for pattern_match:
    -- {"sequence": [1,3,6,10], "answer": 15, "hint": "triangular numbers"}

    -- Difficulty and traits
    difficulty      SMALLINT DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 10),
    primary_trait   VARCHAR(30),                   -- trait this challenge primarily trains
    secondary_trait VARCHAR(30),
    trait_points    JSONB DEFAULT '{}',             -- exact stat points awarded

    -- Timing
    time_limit_secs INTEGER,                       -- null = no time limit

    -- Rewards
    base_xp         INTEGER DEFAULT 10,
    bonus_xp        INTEGER DEFAULT 5,             -- for perfect/fast completion

    -- Ordering
    sort_order      INTEGER DEFAULT 0,

    -- 3D world integration
    scene_id        VARCHAR(50),                   -- Godot scene to load for this challenge

    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_challenges_quest ON challenges(quest_id, sort_order);
CREATE INDEX idx_challenges_type ON challenges(challenge_type);
CREATE INDEX idx_challenges_difficulty ON challenges(difficulty);
CREATE INDEX idx_challenges_trait ON challenges(primary_trait);
```

#### `challenge_options` (for MCQ-type challenges)
```sql
CREATE TABLE challenge_options (
    id              BIGSERIAL PRIMARY KEY,
    challenge_id    BIGINT REFERENCES challenges(id) ON DELETE CASCADE,
    option_text_en  TEXT NOT NULL,
    option_text_ar  TEXT,
    is_correct      BOOLEAN DEFAULT FALSE,
    explanation_en  TEXT,                           -- shown after answering
    explanation_ar  TEXT,
    sort_order      SMALLINT DEFAULT 0
);
```

#### `player_realm_stats`
```sql
CREATE TABLE player_realm_stats (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    realm_id        INTEGER REFERENCES realms(id),

    -- Realm-specific stats
    realm_level     INTEGER DEFAULT 1,
    realm_xp        INTEGER DEFAULT 0,
    stat_points     JSONB DEFAULT '{}',            -- accumulated trait scores

    -- Progress
    quests_completed    INTEGER DEFAULT 0,
    challenges_completed INTEGER DEFAULT 0,
    challenges_perfect  INTEGER DEFAULT 0,          -- completed with max score
    total_time_secs     INTEGER DEFAULT 0,          -- time spent in this realm

    -- Spaced repetition data
    next_review_at      TIMESTAMPTZ,               -- when to re-present challenges
    ease_factor         FLOAT DEFAULT 2.5,          -- SM-2 algorithm ease factor

    -- Visual state (drives 3D world appearance)
    visual_stage    SMALLINT DEFAULT 0,             -- 0=barren, 1-5=progressive bloom

    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(player_id, realm_id)
);
CREATE INDEX idx_realm_stats_player ON player_realm_stats(player_id);
```

#### `player_quest_progress`
```sql
CREATE TABLE player_quest_progress (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    quest_id        BIGINT REFERENCES quests(id),

    status          VARCHAR(20) DEFAULT 'locked',  -- locked, available, in_progress, completed

    -- Challenge tracking within quest
    challenges_total    INTEGER DEFAULT 0,
    challenges_done     INTEGER DEFAULT 0,

    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,

    UNIQUE(player_id, quest_id)
);
CREATE INDEX idx_quest_progress ON player_quest_progress(player_id, status);
```

#### `player_challenge_results`
```sql
CREATE TABLE player_challenge_results (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    challenge_id    BIGINT REFERENCES challenges(id),

    -- Result
    score           SMALLINT CHECK (score BETWEEN 0 AND 100),
    is_correct      BOOLEAN,
    time_taken_secs FLOAT,
    answer_data     JSONB DEFAULT '{}',            -- player's actual answer

    -- XP awarded
    xp_earned       INTEGER DEFAULT 0,
    bonus_earned    INTEGER DEFAULT 0,

    -- Spaced repetition
    review_count    INTEGER DEFAULT 0,             -- times this challenge was repeated
    next_review_at  TIMESTAMPTZ,
    ease_factor     FLOAT DEFAULT 2.5,
    interval_days   INTEGER DEFAULT 1,

    completed_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_challenge_results ON player_challenge_results(player_id, challenge_id);
CREATE INDEX idx_challenge_review ON player_challenge_results(player_id, next_review_at);
```

#### `xp_transactions`
```sql
CREATE TABLE xp_transactions (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),

    amount          INTEGER NOT NULL,
    source          VARCHAR(30) NOT NULL,          -- 'challenge', 'quest', 'daily', 'streak', 'arena', 'feed'
    source_id       BIGINT,                        -- ID of the source object
    realm_id        INTEGER REFERENCES realms(id), -- which realm XP applies to (null=global)

    description     VARCHAR(200),

    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_xp_player ON xp_transactions(player_id, created_at DESC);
```

#### `achievements`
```sql
CREATE TABLE achievements (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    title_en        VARCHAR(200) NOT NULL,
    title_ar        VARCHAR(200),
    description_en  TEXT,
    description_ar  TEXT,
    icon            VARCHAR(50),
    category        VARCHAR(30),                   -- 'realm', 'global', 'social', 'streak', 'special'
    rarity          VARCHAR(20) DEFAULT 'common',  -- common, uncommon, rare, epic, legendary

    -- Unlock condition (evaluated by backend)
    condition_type  VARCHAR(30),                   -- 'quest_complete', 'level_reach', 'streak', 'challenges_count'
    condition_value JSONB DEFAULT '{}',            -- {"quest_id": 5} or {"level": 10} or {"streak": 30}

    -- Reward
    xp_reward       INTEGER DEFAULT 0,

    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `player_achievements`
```sql
CREATE TABLE player_achievements (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    achievement_id  INTEGER REFERENCES achievements(id),
    unlocked_at     TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(player_id, achievement_id)
);
```

#### `daily_streaks`
```sql
CREATE TABLE daily_streaks (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),

    current_streak  INTEGER DEFAULT 0,
    longest_streak  INTEGER DEFAULT 0,
    last_active_date DATE,

    -- Streak freeze (premium feature)
    freeze_count    SMALLINT DEFAULT 0,            -- available freezes

    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(player_id)
);
```

#### `companion_conversations`
```sql
CREATE TABLE companion_conversations (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),

    context         VARCHAR(30) DEFAULT 'chat',    -- 'chat', 'quest_intro', 'quest_outro', 'feedback', 'coaching'
    realm_id        INTEGER REFERENCES realms(id), -- null for general conversations

    -- Companion personality state at time of conversation
    companion_mood  VARCHAR(20) DEFAULT 'neutral', -- neutral, encouraging, challenging, celebratory

    started_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_companion_player ON companion_conversations(player_id, updated_at DESC);
```

#### `companion_messages`
```sql
CREATE TABLE companion_messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES companion_conversations(id) ON DELETE CASCADE,

    role            VARCHAR(10) NOT NULL,           -- 'player', 'companion', 'system'
    content         TEXT NOT NULL,

    -- Metadata
    emotion         VARCHAR(20),                   -- detected/expressed emotion
    tokens_used     INTEGER DEFAULT 0,             -- API token tracking

    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_messages_conv ON companion_messages(conversation_id, created_at);
```

#### `companion_profiles`
```sql
CREATE TABLE companion_profiles (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT UNIQUE REFERENCES players(id),

    -- Evolved personality traits
    warmth          SMALLINT DEFAULT 50,           -- 0=distant, 100=very warm
    directness      SMALLINT DEFAULT 50,           -- 0=gentle, 100=blunt
    humor           SMALLINT DEFAULT 50,           -- 0=serious, 100=playful
    formality       SMALLINT DEFAULT 50,           -- 0=casual, 100=formal
    challenge_level SMALLINT DEFAULT 50,           -- 0=supportive, 100=pushing

    -- Memory/knowledge about the player
    known_strengths     JSONB DEFAULT '[]',
    known_weaknesses    JSONB DEFAULT '[]',
    player_preferences  JSONB DEFAULT '{}',
    interaction_count   INTEGER DEFAULT 0,

    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `feed_items`
```sql
CREATE TABLE feed_items (
    id              BIGSERIAL PRIMARY KEY,

    item_type       VARCHAR(30) NOT NULL,
    -- Types: 'quick_puzzle', 'thought_experiment', 'scenario', 'fact_card',
    --        'quote', 'trivia', 'debate_prompt', 'creative_prompt',
    --        'mindfulness_moment', 'financial_tip', 'social_scenario'

    title_en        VARCHAR(200) NOT NULL,
    title_ar        VARCHAR(200),
    content_en      JSONB NOT NULL,                -- type-specific content
    content_ar      JSONB,

    -- Targeting
    realm_id        INTEGER REFERENCES realms(id),
    difficulty      SMALLINT DEFAULT 5,
    target_traits   JSONB DEFAULT '[]',            -- traits this item exercises

    -- Engagement metrics
    times_shown     INTEGER DEFAULT 0,
    times_completed INTEGER DEFAULT 0,
    avg_rating      FLOAT DEFAULT 0,

    -- Rewards
    xp_reward       INTEGER DEFAULT 5,

    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_feed_realm ON feed_items(realm_id, difficulty);
CREATE INDEX idx_feed_type ON feed_items(item_type);
```

#### `feed_interactions`
```sql
CREATE TABLE feed_interactions (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT REFERENCES players(id),
    feed_item_id    BIGINT REFERENCES feed_items(id),

    action          VARCHAR(20) NOT NULL,          -- 'viewed', 'completed', 'skipped', 'bookmarked'
    answer_data     JSONB DEFAULT '{}',
    score           SMALLINT,
    xp_earned       INTEGER DEFAULT 0,
    time_spent_secs FLOAT,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_feed_interact ON feed_interactions(player_id, created_at DESC);
```

#### `arena_matches` (Phase 2 — schema ready)
```sql
CREATE TABLE arena_matches (
    id              BIGSERIAL PRIMARY KEY,

    match_type      VARCHAR(20) NOT NULL,          -- 'speed', 'strategic', 'mixed', 'team'
    realm_id        INTEGER REFERENCES realms(id),
    status          VARCHAR(20) DEFAULT 'pending', -- pending, active, completed, cancelled

    -- Participants
    player1_id      BIGINT REFERENCES players(id),
    player2_id      BIGINT REFERENCES players(id),
    winner_id       BIGINT REFERENCES players(id),

    -- Results
    player1_score   INTEGER DEFAULT 0,
    player2_score   INTEGER DEFAULT 0,

    -- Match data
    challenges_data JSONB DEFAULT '[]',            -- list of challenge IDs used
    results_data    JSONB DEFAULT '{}',            -- detailed per-challenge results

    -- Rewards
    xp_winner       INTEGER DEFAULT 0,
    xp_loser        INTEGER DEFAULT 0,
    rating_change   INTEGER DEFAULT 0,             -- ELO-like rating change

    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `player_arena_stats` (Phase 2)
```sql
CREATE TABLE player_arena_stats (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT UNIQUE REFERENCES players(id),

    rating          INTEGER DEFAULT 1000,          -- ELO-like rating
    rank_tier       VARCHAR(20) DEFAULT 'bronze',  -- bronze, silver, gold, platinum, diamond, legend

    wins            INTEGER DEFAULT 0,
    losses          INTEGER DEFAULT 0,
    draws           INTEGER DEFAULT 0,
    win_streak      INTEGER DEFAULT 0,
    best_win_streak INTEGER DEFAULT 0,

    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. Django Backend Structure

### Project Layout
```
mindarena-backend/
├── manage.py
├── requirements.txt
├── Procfile                         # Railway deployment
├── railway.toml
├── .env.example
├── .gitignore
│
├── config/                          # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                  # Shared settings
│   │   ├── development.py           # Local dev settings
│   │   └── production.py            # Railway production settings
│   ├── urls.py                      # Root URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── accounts/                    # User auth & profiles
│   │   ├── models.py                # Player, CompanionProfile
│   │   ├── serializers.py
│   │   ├── views.py                 # Register, login, profile CRUD
│   │   ├── urls.py
│   │   └── services.py              # Auth logic, token management
│   │
│   ├── assessment/                  # Personality assessment
│   │   ├── models.py                # PersonalityAssessment
│   │   ├── serializers.py
│   │   ├── views.py                 # Submit assessment, get results
│   │   ├── urls.py
│   │   ├── services.py              # Scoring algorithms (Big Five, EQ)
│   │   └── data/
│   │       ├── questions_en.json    # Assessment questions (English)
│   │       └── questions_ar.json    # Assessment questions (Arabic)
│   │
│   ├── realms/                      # Realms, quests, challenges
│   │   ├── models.py                # Realm, Quest, Challenge, ChallengeOption
│   │   ├── serializers.py
│   │   ├── views.py                 # Realm list, quest list, challenge detail
│   │   ├── urls.py
│   │   ├── services.py              # Quest unlocking logic, challenge validation
│   │   └── data/
│   │       ├── realms_seed.json     # Initial realm data
│   │       ├── quests_seed.json     # Initial quest data
│   │       └── challenges/          # Challenge content JSON files
│   │           ├── logic_*.json
│   │           ├── emotion_*.json
│   │           └── creativity_*.json
│   │
│   ├── progression/                 # XP, levels, stats, achievements
│   │   ├── models.py                # PlayerRealmStat, XPTransaction, Achievement, etc.
│   │   ├── serializers.py
│   │   ├── views.py                 # Stats dashboard, achievements, leaderboard
│   │   ├── urls.py
│   │   ├── services.py              # XP calculation, level-up logic, achievement checks
│   │   └── constants.py             # XP curve formulas, level thresholds
│   │
│   ├── companion/                   # AI companion
│   │   ├── models.py                # CompanionConversation, CompanionMessage
│   │   ├── serializers.py
│   │   ├── views.py                 # Chat endpoint, companion state
│   │   ├── urls.py
│   │   ├── services.py              # Claude API integration, prompt engineering
│   │   └── prompts/
│   │       ├── system_prompt.txt    # Base companion personality
│   │       ├── coaching.txt         # Coaching mode prompt
│   │       └── quest_dialogue.txt   # Quest narrative prompts
│   │
│   ├── feed/                        # Anti-scroll feed
│   │   ├── models.py                # FeedItem, FeedInteraction
│   │   ├── serializers.py
│   │   ├── views.py                 # Personalized feed, submit interaction
│   │   ├── urls.py
│   │   ├── services.py              # Feed personalization algorithm
│   │   └── data/
│   │       └── feed_items_seed.json # Initial feed content
│   │
│   └── arena/                       # Competitive mode (Phase 2)
│       ├── models.py                # ArenaMatch, PlayerArenaStats
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── services.py              # Matchmaking, ELO calculation
│
├── core/                            # Shared utilities
│   ├── middleware.py                 # Request logging, language detection
│   ├── permissions.py               # Custom DRF permissions
│   ├── pagination.py                # Custom pagination
│   ├── exceptions.py                # Custom exception handlers
│   └── utils.py                     # Shared helper functions
│
└── seed/                            # Management commands
    └── management/
        └── commands/
            ├── seed_realms.py       # Seed realm data
            ├── seed_challenges.py   # Seed challenge content
            ├── seed_feed.py         # Seed feed items
            └── seed_achievements.py # Seed achievements
```

### Django Models (Python)

```python
# apps/accounts/models.py
class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player')
    display_name = models.CharField(max_length=50)
    avatar_preset = models.CharField(max_length=30, default='default')
    avatar_colors = models.JSONField(default=dict)
    overall_level = models.IntegerField(default=1)
    total_xp = models.BigIntegerField(default=0)
    premium_tier = models.CharField(max_length=20, default='free')
    preferred_lang = models.CharField(max_length=5, default='en')
    onboarding_done = models.BooleanField(default=False)
    last_active_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# apps/progression/services.py
class XPService:
    """
    XP Curve: XP needed for level N = floor(100 * N^1.5)
    Level 1:  100 XP
    Level 2:  283 XP
    Level 5:  1118 XP
    Level 10: 3162 XP
    Level 20: 8944 XP
    Level 50: 35355 XP
    """
    @staticmethod
    def xp_for_level(level: int) -> int:
        return int(100 * (level ** 1.5))

    @staticmethod
    def level_from_xp(total_xp: int) -> int:
        level = 1
        while XPService.xp_for_level(level + 1) <= total_xp:
            level += 1
        return level

    @staticmethod
    def award_xp(player, amount, source, source_id=None, realm=None):
        """Award XP, check level up, check achievements."""
        pass  # Full implementation in development
```

---

## 5. API Endpoints

### Authentication
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register/` | Create account |
| POST | `/api/auth/login/` | Get JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| POST | `/api/auth/logout/` | Invalidate tokens |
| GET | `/api/auth/me/` | Get current player profile |

### Player Profile
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/profile/` | Full player profile with stats |
| PATCH | `/api/profile/` | Update display name, avatar, preferences |
| GET | `/api/profile/stats/` | Radar chart data (all 8 realm stats) |
| GET | `/api/profile/stats/history/` | Stat changes over time |
| GET | `/api/profile/achievements/` | Player's unlocked achievements |

### Personality Assessment
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/assessment/questions/` | Get assessment questions |
| POST | `/api/assessment/submit/` | Submit assessment answers |
| GET | `/api/assessment/results/` | Get latest assessment results |
| GET | `/api/assessment/history/` | All past assessments (track growth) |

### Realms & Quests
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/realms/` | List all realms with player stats |
| GET | `/api/realms/{slug}/` | Realm detail with quests |
| GET | `/api/realms/{slug}/quests/` | Quests for a realm |
| GET | `/api/quests/{id}/` | Quest detail with challenges |
| POST | `/api/quests/{id}/start/` | Start a quest |

### Challenges
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/challenges/{id}/` | Get challenge content |
| POST | `/api/challenges/{id}/submit/` | Submit challenge answer |
| GET | `/api/challenges/review/` | Get challenges due for review (spaced repetition) |

### AI Companion
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/companion/chat/` | Send message, get AI response |
| GET | `/api/companion/conversations/` | List recent conversations |
| GET | `/api/companion/profile/` | Companion personality state |
| POST | `/api/companion/quest-dialogue/` | Get quest intro/outro dialogue |

### Feed
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/feed/` | Get personalized feed (paginated) |
| POST | `/api/feed/{id}/interact/` | Record interaction (completed, skipped) |
| POST | `/api/feed/{id}/bookmark/` | Bookmark feed item |

### Progression
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/progression/dashboard/` | Full progression overview |
| GET | `/api/progression/leaderboard/` | Global/realm leaderboards |
| GET | `/api/progression/streak/` | Current streak info |
| GET | `/api/progression/xp-history/` | Recent XP transactions |

### Health
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health/` | Backend health check |

---

## 6. Godot Game Client Structure

### Project Layout
```
mindarena-game/
├── project.godot                    # Godot project file
├── export_presets.cfg               # Web, Android export configs
│
├── assets/
│   ├── models/                      # 3D models (.glb)
│   │   ├── characters/
│   │   │   ├── player_avatar.glb
│   │   │   └── companion.glb
│   │   ├── environments/
│   │   │   ├── hub_world.glb
│   │   │   ├── logic_fortress.glb
│   │   │   ├── emotion_ocean.glb
│   │   │   └── creativity_nebula.glb
│   │   └── props/
│   │       ├── challenge_node.glb   # Glowing challenge station
│   │       ├── portal.glb           # Realm entry portals
│   │       └── collectibles/
│   │
│   ├── textures/
│   │   ├── skyboxes/
│   │   ├── terrain/
│   │   ├── ui/
│   │   └── particles/
│   │
│   ├── audio/
│   │   ├── music/
│   │   │   ├── hub_ambient.ogg
│   │   │   ├── logic_fortress.ogg
│   │   │   ├── emotion_ocean.ogg
│   │   │   ├── creativity_nebula.ogg
│   │   │   └── challenge_active.ogg
│   │   ├── sfx/
│   │   │   ├── xp_gain.ogg
│   │   │   ├── level_up.ogg
│   │   │   ├── challenge_complete.ogg
│   │   │   ├── challenge_fail.ogg
│   │   │   ├── portal_enter.ogg
│   │   │   ├── ui_click.ogg
│   │   │   └── companion_speak.ogg
│   │   └── ambient/
│   │       ├── wind.ogg
│   │       ├── water.ogg
│   │       └── crystal_hum.ogg
│   │
│   ├── fonts/
│   │   ├── main_en.ttf
│   │   └── main_ar.ttf             # Arabic-supporting font
│   │
│   └── shaders/
│       ├── realm_transition.gdshader
│       ├── glow_pulse.gdshader      # Challenge node glow
│       ├── water_surface.gdshader
│       └── growth_effect.gdshader   # Visual transformation
│
├── scenes/
│   ├── main.tscn                    # Root scene (scene manager)
│   ├── ui/
│   │   ├── loading_screen.tscn
│   │   ├── main_menu.tscn
│   │   ├── hud.tscn                 # In-game HUD (XP bar, level, realm)
│   │   ├── pause_menu.tscn
│   │   ├── profile_screen.tscn      # Stats radar chart, achievements
│   │   ├── feed_screen.tscn         # Anti-scroll feed
│   │   ├── companion_chat.tscn      # AI chat overlay
│   │   ├── challenge_ui.tscn        # Challenge overlay (MCQ, scenario, etc.)
│   │   ├── assessment_ui.tscn       # Personality quiz UI
│   │   ├── settings_screen.tscn
│   │   └── components/
│   │       ├── stat_bar.tscn
│   │       ├── achievement_card.tscn
│   │       ├── feed_card.tscn
│   │       ├── quest_card.tscn
│   │       └── radar_chart.tscn
│   │
│   ├── world/
│   │   ├── hub_world.tscn           # Central mind hub
│   │   ├── logic_fortress.tscn      # Realm 1
│   │   ├── emotion_ocean.tscn       # Realm 2
│   │   ├── creativity_nebula.tscn   # Realm 3
│   │   └── challenge_zones/
│   │       ├── spatial_puzzle.tscn
│   │       ├── timed_trial.tscn
│   │       └── scenario_room.tscn
│   │
│   └── characters/
│       ├── player.tscn              # Player character + controller
│       └── companion.tscn           # AI companion NPC
│
├── scripts/
│   ├── autoload/                    # Singletons (Godot autoload)
│   │   ├── game_manager.gd          # Global game state
│   │   ├── api_client.gd            # HTTP requests to Django API
│   │   ├── auth_manager.gd          # JWT token management
│   │   ├── player_data.gd           # Local player data cache
│   │   ├── scene_manager.gd         # Scene transitions
│   │   ├── audio_manager.gd         # Music/SFX management
│   │   └── localization.gd          # EN/AR string management
│   │
│   ├── player/
│   │   ├── player_controller.gd     # 3D movement, camera, input
│   │   ├── player_camera.gd         # Third-person camera
│   │   └── player_animation.gd      # Animation state machine
│   │
│   ├── companion/
│   │   ├── companion_controller.gd  # Follow player, pathfinding
│   │   ├── companion_dialogue.gd    # Dialogue bubble triggers
│   │   └── companion_animation.gd
│   │
│   ├── world/
│   │   ├── realm_manager.gd         # Realm loading, visual state
│   │   ├── challenge_node.gd        # Interactable challenge station
│   │   ├── portal.gd                # Realm entry portal
│   │   ├── world_transformer.gd     # Visual transformation system
│   │   └── npc_marker.gd            # Quest/info markers
│   │
│   ├── challenges/
│   │   ├── challenge_manager.gd     # Load, present, validate challenges
│   │   ├── mcq_challenge.gd         # Multiple choice logic
│   │   ├── spatial_puzzle.gd        # 3D spatial puzzle logic
│   │   ├── timed_challenge.gd       # Timed response challenges
│   │   ├── scenario_challenge.gd    # Ethical/emotional scenarios
│   │   └── pattern_challenge.gd     # Pattern matching
│   │
│   ├── ui/
│   │   ├── feed_controller.gd       # Feed scrolling, interaction
│   │   ├── chat_controller.gd       # Companion chat UI
│   │   ├── hud_controller.gd        # XP bar, notifications
│   │   ├── radar_chart.gd           # Custom radar chart drawing
│   │   └── assessment_controller.gd # Personality quiz flow
│   │
│   └── data/
│       ├── models.gd                # Data classes (Player, Quest, etc.)
│       └── constants.gd             # Game constants, XP formulas
│
└── addons/                          # Godot plugins (if any)
```

### Key Godot Scripts

#### `api_client.gd` — Communication with Django
```gdscript
# scripts/autoload/api_client.gd
extends Node

const BASE_URL = "https://mindarena-api.railway.app"
var access_token: String = ""
var refresh_token: String = ""

signal request_completed(response_data)
signal request_failed(error_message)

func _make_request(method: String, endpoint: String, body: Dictionary = {}) -> Dictionary:
    var http = HTTPRequest.new()
    add_child(http)

    var headers = [
        "Content-Type: application/json",
        "Accept-Language: %s" % PlayerData.language
    ]
    if access_token:
        headers.append("Authorization: Bearer %s" % access_token)

    var url = BASE_URL + endpoint
    var json_body = JSON.stringify(body) if body else ""

    http.request(url, headers, HTTPClient.METHOD_POST if method == "POST" else HTTPClient.METHOD_GET, json_body)

    var result = await http.request_completed
    http.queue_free()

    # Parse response
    var response = JSON.parse_string(result[3].get_string_from_utf8())

    # Handle token refresh if 401
    if result[1] == 401:
        await _refresh_token()
        return await _make_request(method, endpoint, body)

    return response

# Auth
func login(username: String, password: String) -> Dictionary:
    return await _make_request("POST", "/api/auth/login/", {"username": username, "password": password})

func register(username: String, email: String, password: String) -> Dictionary:
    return await _make_request("POST", "/api/auth/register/", {"username": username, "email": email, "password": password})

# Profile
func get_profile() -> Dictionary:
    return await _make_request("GET", "/api/profile/")

func get_stats() -> Dictionary:
    return await _make_request("GET", "/api/profile/stats/")

# Realms
func get_realms() -> Array:
    var data = await _make_request("GET", "/api/realms/")
    return data.get("results", [])

# Challenges
func get_challenge(id: int) -> Dictionary:
    return await _make_request("GET", "/api/challenges/%d/" % id)

func submit_challenge(id: int, answer_data: Dictionary) -> Dictionary:
    return await _make_request("POST", "/api/challenges/%d/submit/" % id, answer_data)

# Companion
func send_companion_message(message: String, context: String = "chat") -> Dictionary:
    return await _make_request("POST", "/api/companion/chat/", {"message": message, "context": context})

# Feed
func get_feed(page: int = 1) -> Array:
    var data = await _make_request("GET", "/api/feed/?page=%d" % page)
    return data.get("results", [])
```

#### `player_controller.gd` — 3D Character Movement
```gdscript
# scripts/player/player_controller.gd
extends CharacterBody3D

@export var speed := 5.0
@export var jump_velocity := 4.5
@export var rotation_speed := 10.0

var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")
var input_dir := Vector2.ZERO
var is_near_challenge := false
var nearby_challenge_node = null

@onready var camera_pivot = $CameraPivot
@onready var model = $Model
@onready var interaction_label = $InteractionLabel

func _physics_process(delta):
    # Gravity
    if not is_on_floor():
        velocity.y -= gravity * delta

    # Jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = jump_velocity

    # Movement
    input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction = (camera_pivot.global_basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()

    if direction:
        velocity.x = direction.x * speed
        velocity.z = direction.z * speed
        # Rotate model toward movement direction
        var target_rotation = atan2(direction.x, direction.z)
        model.rotation.y = lerp_angle(model.rotation.y, target_rotation, rotation_speed * delta)
    else:
        velocity.x = move_toward(velocity.x, 0, speed)
        velocity.z = move_toward(velocity.z, 0, speed)

    move_and_slide()

    # Interaction
    if is_near_challenge and Input.is_action_just_pressed("interact"):
        _start_challenge()

func _on_interaction_area_entered(area):
    if area.is_in_group("challenge_nodes"):
        is_near_challenge = true
        nearby_challenge_node = area.get_parent()
        interaction_label.show()
        interaction_label.text = "Press E to start challenge"

func _on_interaction_area_exited(area):
    if area.is_in_group("challenge_nodes"):
        is_near_challenge = false
        nearby_challenge_node = null
        interaction_label.hide()

func _start_challenge():
    if nearby_challenge_node:
        GameManager.start_challenge(nearby_challenge_node.challenge_id)
```

---

## 7. Personality Assessment System

### Framework: Hybrid Big Five + EQ + Cognitive Baseline

The assessment maps to 14 internal traits that feed into the 8 realm stats:

#### Big Five (OCEAN) — 5 traits
Each measured by 4 scenario-based questions (20 questions total)

| Trait | Description | Maps to Realm |
|-------|-------------|---------------|
| Openness | Curiosity, creativity, adventurousness | Creativity Nebula |
| Conscientiousness | Organization, discipline, persistence | Discipline Citadel |
| Extraversion | Energy from social interaction, assertiveness | Social Bridge |
| Agreeableness | Cooperation, empathy, trust | Emotion Ocean |
| Neuroticism | Emotional reactivity, stress response | Wellness Grove |

#### EQ Components — 5 traits
Each measured by 3 scenario-based questions (15 questions total)

| Trait | Description | Maps to Realm |
|-------|-------------|---------------|
| Self-Awareness | Recognizing own emotions | Emotion Ocean |
| Self-Regulation | Managing emotions, impulse control | Discipline Citadel |
| Motivation | Internal drive, goal pursuit | Discipline Citadel |
| Empathy | Understanding others' emotions | Social Bridge |
| Social Skills | Relationship management, influence | Social Bridge |

#### Cognitive Baseline — 4 traits
Each measured by 2-3 quick cognitive tests (10 tests total)

| Trait | Test Type | Maps to Realm |
|-------|-----------|---------------|
| Logical Reasoning | Pattern sequences, syllogisms | Logic Fortress |
| Creative Thinking | Divergent thinking, unusual uses | Creativity Nebula |
| Processing Speed | Rapid categorization, reaction time | Logic Fortress |
| Working Memory | Sequence recall, n-back test | Knowledge Peaks |

#### Total Assessment: ~45 items, ~5-7 minutes

#### Scoring
```python
# Each question has weighted scores for relevant traits
# Example scenario question for Empathy:
{
    "type": "scenario_choice",
    "scenario": "Your friend cancels plans at the last minute, saying they're 'just tired.' You notice they've seemed off lately.",
    "choices": [
        {"text": "Tell them it's fine and ask if they want to talk about what's really going on", "scores": {"empathy": 4, "social_skills": 3}},
        {"text": "Say no problem and suggest rescheduling for next week", "scores": {"empathy": 2, "agreeableness": 3}},
        {"text": "Express disappointment but accept their reason", "scores": {"empathy": 1, "self_awareness": 2}},
        {"text": "Text back 'ok' and make other plans", "scores": {"empathy": 0, "self_regulation": 1}}
    ]
}

# Scores normalized to 0-100 scale per trait
# Trait scores combined into realm power scores:
# Realm Score = weighted average of contributing traits
# Logic Fortress = 0.6 * logical_reasoning + 0.4 * processing_speed
# Emotion Ocean = 0.3 * self_awareness + 0.3 * empathy + 0.2 * agreeableness + 0.2 * self_regulation
# etc.
```

#### Realm Score Formulas
```
Logic Fortress    = 0.50 * logical_reasoning + 0.30 * processing_speed + 0.20 * working_memory
Emotion Ocean     = 0.30 * self_awareness + 0.25 * empathy + 0.25 * self_regulation + 0.20 * agreeableness
Creativity Nebula = 0.60 * creative_thinking + 0.25 * openness + 0.15 * working_memory
Discipline Citadel= 0.40 * conscientiousness + 0.30 * self_regulation + 0.30 * motivation
Knowledge Peaks   = 0.50 * working_memory + 0.30 * logical_reasoning + 0.20 * processing_speed
Social Bridge     = 0.30 * social_skills + 0.25 * extraversion + 0.25 * empathy + 0.20 * agreeableness
Wealth Garden     = 0.40 * logical_reasoning + 0.30 * conscientiousness + 0.30 * self_regulation
Wellness Grove    = 0.35 * self_awareness + 0.35 * self_regulation + 0.30 * (100 - neuroticism)
```

---

## 8. Challenge & Quest System

### Challenge Types per Realm

#### Logic Fortress Challenges
| Type | Description | Gameplay |
|------|-------------|----------|
| Pattern Sequence | Complete the number/shape pattern | Player selects next item in sequence |
| Syllogism | Evaluate logical arguments | "Is this conclusion valid?" with reasoning |
| Spatial Rotation | Identify rotated 3D objects | 3D puzzle in the game world |
| Logic Grid | Solve constraint puzzles | Interactive grid with clue elimination |
| Code Tracing | Follow algorithm steps | Step through visual pseudocode |
| Probability | Estimate likelihoods | Scenario-based probability questions |

#### Emotion Ocean Challenges
| Type | Description | Gameplay |
|------|-------------|----------|
| Emotion Reading | Identify emotions from scenarios | Read situation, select correct emotion |
| Conflict Resolution | Handle interpersonal conflicts | Choose best response, scored on EQ |
| Self-Reflection | Journal/reflection prompts | Open-text with AI evaluation |
| Empathy Mapping | Understand multiple perspectives | Map out how each person in scenario feels |
| Stress Scenario | Handle high-pressure situations | Timed scenario with physiological awareness |
| Emotional Vocabulary | Name nuanced emotions | Match scenarios to precise emotion words |

#### Creativity Nebula Challenges
| Type | Description | Gameplay |
|------|-------------|----------|
| Divergent Thinking | Generate multiple uses for objects | Timed brainstorm, scored on uniqueness |
| Story Completion | Complete an unfinished story | Creative writing with AI evaluation |
| Visual Puzzle | See hidden images/connections | Find creative associations |
| Problem Reframing | Solve by changing perspective | Lateral thinking puzzles |
| Combination | Combine unrelated concepts | Create meaningful connections |
| Design Challenge | Design a solution to a problem | Describe/sketch, AI evaluates creativity |

### Quest Structure

Each realm has quest chains structured as:

```
Main Quest Chain (10 quests per realm):
  Quest 1: "Arrival" (tutorial, 3 easy challenges)
  Quest 2: "First Steps" (4 challenges, difficulty 2-3)
  Quest 3: "Growing Stronger" (4 challenges, difficulty 3-4)
  Quest 4: "The Trial" (5 challenges, difficulty 4-5, boss challenge)
  Quest 5: "Deeper Understanding" (4 challenges, difficulty 5-6)
  Quest 6-9: Progressive difficulty increase
  Quest 10: "Realm Mastery" (3 hard challenges + boss, difficulty 8-10)

Side Quests: Unlocked after completing main quest milestones
Daily Quests: 3 random challenges per day, any realm, bonus XP
```

### Challenge Content JSON Example
```json
{
    "slug": "logic_pattern_01",
    "challenge_type": "pattern_sequence",
    "difficulty": 3,
    "primary_trait": "logical_reasoning",
    "time_limit_secs": 45,
    "base_xp": 15,
    "bonus_xp": 10,
    "content": {
        "instruction_en": "What comes next in this sequence?",
        "instruction_ar": "ما الذي يأتي بعد ذلك في هذا التسلسل؟",
        "sequence": [2, 6, 12, 20, 30],
        "options": [40, 42, 44, 38],
        "correct_index": 1,
        "explanation_en": "The differences are 4, 6, 8, 10, 12 — each difference increases by 2. So 30 + 12 = 42.",
        "explanation_ar": "الفروق هي 4، 6، 8، 10، 12 — كل فرق يزيد بمقدار 2. إذن 30 + 12 = 42.",
        "hint_en": "Look at the differences between consecutive numbers.",
        "trait_points": {"logical_reasoning": 3, "processing_speed": 1}
    }
}
```

---

## 9. Progression & XP System

### XP Curve Formula
```
XP needed for level N = floor(100 * N^1.5)

Level 1:    100 XP
Level 2:    283 XP
Level 3:    520 XP
Level 5:    1,118 XP
Level 10:   3,162 XP
Level 15:   5,809 XP
Level 20:   8,944 XP
Level 30:   16,432 XP
Level 50:   35,355 XP
Level 100:  100,000 XP
```

### XP Sources
| Source | Base XP | Notes |
|--------|---------|-------|
| Challenge (easy) | 10-15 | +5 bonus for perfect/fast |
| Challenge (medium) | 20-30 | +10 bonus |
| Challenge (hard) | 40-60 | +20 bonus |
| Quest completion | 50-200 | Scales with quest length |
| Daily quest set | 30 | 3 challenges, any realm |
| Streak bonus | 5-50 | Scales: day 1=5, day 7=15, day 30=50 |
| Feed interaction | 3-8 | Per feed item completed |
| Assessment complete | 100 | One-time per assessment |
| Achievement unlock | 20-100 | Varies by achievement rarity |

### Streak System
```
Day 1-6:   5 XP per day
Day 7:     15 XP (weekly milestone)
Day 8-13:  8 XP per day
Day 14:    25 XP (2-week milestone)
Day 15-29: 10 XP per day
Day 30:    50 XP (monthly milestone)
Day 31+:   12 XP per day
Day 60:    75 XP
Day 90:    100 XP
Day 365:   500 XP (yearly milestone)
```

### Visual World Transformation Stages
Each realm has 6 visual stages based on realm level:

| Stage | Realm Level | Visual State |
|-------|-------------|-------------|
| 0 | 1 | Barren, dark, minimal detail |
| 1 | 3 | First signs of life (small lights, tiny growth) |
| 2 | 6 | Active growth (plants/crystals/structures forming) |
| 3 | 10 | Established (full environment, active elements) |
| 4 | 15 | Flourishing (particle effects, rich detail) |
| 5 | 20 | Mastery (full bloom, spectacular, unique effects) |

### Achievement Categories

#### Realm Achievements
- "First Steps" — Complete first challenge in any realm
- "Logic Apprentice/Adept/Master" — Reach realm level 5/10/20 in Logic Fortress
- (Same pattern for all 8 realms = 24 realm achievements)

#### Progress Achievements
- "Rising Mind" — Reach overall level 5
- "Expanding Horizons" — Unlock 3 realms
- "Mind Architect" — Unlock all 8 realms
- "Century" — Reach overall level 100

#### Streak Achievements
- "Consistent" — 7-day streak
- "Dedicated" — 30-day streak
- "Unstoppable" — 90-day streak
- "Year of Growth" — 365-day streak

#### Special Achievements
- "Self-Aware" — Complete personality assessment
- "Evolution" — Show measurable improvement on reassessment
- "Balanced Mind" — All 8 realm stats above 50
- "Perfect Score" — Complete any challenge with 100% score in under half the time limit
- "Night Owl" — Complete 10 challenges between midnight and 5 AM
- "Early Bird" — Complete 10 challenges between 5 AM and 8 AM

---

## 10. AI Companion Architecture

### System Prompt (base personality)
```
You are the player's AI companion in MindArena, a self-development game.
You exist within the player's inner mind world as a guiding presence.

PLAYER PROFILE:
- Name: {player_name}
- Level: {overall_level}
- Strongest realm: {strongest_realm} (level {strongest_level})
- Weakest realm: {weakest_realm} (level {weakest_level})
- Personality: {big_five_summary}
- Recent activity: {recent_summary}

YOUR PERSONALITY (adapts over time):
- Warmth: {warmth}/100
- Directness: {directness}/100
- Humor: {humor}/100
- Formality: {formality}/100
- Challenge Level: {challenge_level}/100

RULES:
1. Keep responses concise (2-4 sentences for casual chat, longer for coaching)
2. Reference the player's actual stats and progress
3. Gently encourage exploration of weaker realms
4. Celebrate genuine progress, don't give empty praise
5. Adapt your tone based on your personality values above
6. Use the player's preferred language ({preferred_lang})
7. Never break character — you ARE their mind's guide
8. For coaching mode, ask reflective questions rather than lecturing
```

### Companion Personality Evolution
```python
# After each interaction, adjust companion personality slightly:
def evolve_companion(companion_profile, interaction_data):
    """Evolve companion personality based on player interactions."""
    # If player responds well to humor → increase humor
    # If player asks deep questions → increase directness, decrease formality
    # If player seems frustrated → increase warmth, decrease challenge_level
    # If player is coasting → increase challenge_level

    # Each trait shifts by max 1 point per interaction
    # Range: 0-100, drift toward player's preferred style

    if interaction_data['player_sentiment'] == 'positive':
        # Reinforce current style
        pass
    elif interaction_data['player_sentiment'] == 'frustrated':
        companion_profile.warmth = min(100, companion_profile.warmth + 1)
        companion_profile.challenge_level = max(0, companion_profile.challenge_level - 1)

    companion_profile.interaction_count += 1
    companion_profile.save()
```

### Conversation Contexts
| Context | When Triggered | Companion Behavior |
|---------|---------------|-------------------|
| `chat` | Player opens chat | Open conversation, coaching, reflection |
| `quest_intro` | Starting a quest | Sets the scene, explains what's ahead |
| `quest_outro` | Completing a quest | Celebrates, reflects on what was learned |
| `challenge_hint` | Player requests hint | Gives a nudge without full answer |
| `feedback` | After challenge result | Comments on performance, suggests improvement |
| `coaching` | Player asks for advice | Socratic questioning, deeper reflection |
| `check_in` | Daily login | Welcomes back, suggests today's focus |

---

## 11. Feed System

### Personalization Algorithm
```python
def get_personalized_feed(player, page=1, per_page=10):
    """
    Feed personalization based on:
    1. Weakest realms (40% weight) — push growth where needed
    2. Preferred difficulty (30% weight) — flow state maintenance
    3. Content variety (20% weight) — don't repeat types
    4. Freshness (10% weight) — unseen items first
    """

    # Get player's realm stats, sorted weakest first
    weak_realms = PlayerRealmStat.objects.filter(player=player).order_by('realm_level')

    # Target difficulty = player's average realm level ± 1
    avg_level = weak_realms.aggregate(avg=Avg('realm_level'))['avg'] or 1
    target_difficulty = max(1, min(10, int(avg_level)))

    # Get recently seen item IDs
    recent_ids = FeedInteraction.objects.filter(
        player=player
    ).order_by('-created_at')[:50].values_list('feed_item_id', flat=True)

    # Score each feed item
    items = FeedItem.objects.filter(is_active=True).exclude(id__in=recent_ids)

    scored_items = []
    for item in items:
        score = 0
        # Weak realm bonus
        if item.realm_id in [r.realm_id for r in weak_realms[:3]]:
            score += 40
        # Difficulty match bonus
        diff_gap = abs(item.difficulty - target_difficulty)
        score += max(0, 30 - diff_gap * 10)
        # Variety bonus (check last 10 interactions for type diversity)
        score += 20  # simplified
        # Freshness
        score += 10
        scored_items.append((score, item))

    scored_items.sort(key=lambda x: -x[0])

    # Paginate
    start = (page - 1) * per_page
    return [item for _, item in scored_items[start:start + per_page]]
```

### Feed Item Types (MVP)

| Type | Format | Interaction | XP |
|------|--------|-------------|-----|
| Quick Puzzle | Logic/math problem | Select answer | 5 |
| Thought Experiment | "What if..." scenario | Choose response | 5 |
| Scenario Card | Emotional/social situation | Rate best response | 5 |
| Fact + Question | Interesting fact → follow-up question | Answer question | 3 |
| Quote + Reflection | Inspirational quote → reflection prompt | Text input | 8 |
| Trivia | General knowledge | Multiple choice | 3 |
| Debate Prompt | Controversial topic | Choose a side, justify | 8 |
| Creative Prompt | "Describe/imagine..." | Text input | 8 |
| Mindfulness Moment | Breathing exercise or body scan | Complete timer | 5 |
| Financial Decision | Budget/investment scenario | Make the choice | 5 |

---

## 12. Visual Design & 3D World

### Art Direction
- **Style**: Clean, low-poly, stylized — inspired by Monument Valley, Journey, Abzu
- **Palette**: Each realm has a distinct color scheme
- **Lighting**: Dramatic, atmospheric — volumetric fog, god rays, soft shadows
- **Geometry**: Abstract, surreal — floating islands, impossible architecture, organic forms

### Realm Color Palettes

| Realm | Primary | Secondary | Accent | Atmosphere |
|-------|---------|-----------|--------|-----------|
| Hub World | #1a1a2e | #16213e | #e94560 | Deep space, starfield |
| Logic Fortress | #0a3d62 | #3c6382 | #82ccdd | Crystalline, structured, blue |
| Emotion Ocean | #6c5ce7 | #a29bfe | #fd79a8 | Fluid, warm purples, pink light |
| Creativity Nebula | #fdcb6e | #e17055 | #00b894 | Colorful, swirling, dynamic |
| Discipline Citadel | #2d3436 | #636e72 | #dfe6e9 | Stone, iron, silver, ordered |
| Knowledge Peaks | #0c2461 | #1e3799 | #f6e58d | Mountain, golden light, ancient |
| Social Bridge | #e55039 | #eb4d4b | #f9ca24 | Warm, connected, bridges |
| Wealth Garden | #27ae60 | #2ecc71 | #f1c40f | Lush green, golden, growing |
| Wellness Grove | #00b894 | #55efc4 | #ffeaa7 | Natural, peaceful, healing |

### Visual Transformation System

Each realm environment has 6 LOD-like stages:

**Stage 0 (Barren)**:
- Flat, dark terrain
- No vegetation/decoration
- Dim lighting, fog
- Silent ambiance

**Stage 5 (Mastery)**:
- Rich terrain with detail
- Full vegetation/crystal/structure growth
- Dynamic lighting, particles
- Active ambient life (floating particles, gentle motion)
- Unique realm-specific spectacular effect

The transformation is driven by `visual_stage` in `player_realm_stats` and implemented via Godot shader parameters and node visibility groups.

---

## 13. Realm Designs

### Hub World — "The Mindscape"
- Central floating island in space
- 8 portals arranged in a circle, each glowing with realm colors
- Portal visual intensity = realm level (dim for barren, bright for mastered)
- AI companion waits here
- Profile/stats viewable from center pedestal
- Skybox: deep space with slowly rotating nebula
- Music: ambient, contemplative, mysterious

### Logic Fortress
- Crystalline floating fortress with geometric architecture
- Platforms connected by light bridges
- Challenge nodes embedded in crystal walls
- Puzzles are 3D spatial challenges within the crystal structures
- Sound: crystalline tones, mathematical harmonics
- Transformation: crystals grow, new bridges form, light intensifies

### Emotion Ocean
- Vast ocean with floating lily pad islands
- Water color shifts based on challenge themes (warm for empathy, cool for self-regulation)
- Challenge nodes are glowing orbs hovering over water
- Jellyfish-like particles float around
- Sound: gentle waves, ethereal vocals
- Transformation: ocean calms, bioluminescence increases, new islands surface

### Creativity Nebula
- Open space with colorful gas clouds
- Player floats/flies between creative stations
- Paint splatter particles, shifting colors
- Challenge nodes are exploding stars of color
- Sound: playful, unexpected, generative
- Transformation: nebula expands, new colors appear, impossible geometry forms

---

## 14. Character System

### Player Avatar
- **Preset system** (MVP): 8-10 base character presets
- **Customization**: Colors (skin, hair, outfit) via color picker
- **Animations**: Idle, walk, run, jump, interact, celebrate, think
- **Appearance evolution**: Subtle visual changes as overall level increases (glow, aura, outfit details)

### AI Companion
- **Appearance**: Abstract/ethereal being (floating light form, wisps)
- **Not human**: Deliberately non-human to feel like a mind entity
- **Visual adaptations**: Companion's visual appearance subtly shifts based on its evolved personality traits
- **Animations**: Float, pulse, react (happy, concerned, excited), point direction

---

## 15. Audio & Music

### Music Strategy
- Each realm: unique ambient music track (loopable, 3-5 minutes)
- Hub: separate ambient track
- Challenge active: subtle intensity increase overlay
- Level up: celebratory sting
- All music: original composition or royalty-free (Pixabay, Freesound, OpenGameArt)

### SFX List (MVP)
| Sound | Trigger |
|-------|---------|
| ui_click | Any UI button press |
| ui_hover | Button hover |
| challenge_start | Challenge activates |
| challenge_correct | Correct answer |
| challenge_wrong | Wrong answer |
| challenge_complete | All challenges in quest done |
| xp_gain | XP awarded (ascending chime) |
| level_up | Level increase (fanfare) |
| portal_enter | Enter realm portal |
| portal_ambient | Portal proximity |
| companion_speak | AI companion message appears |
| world_transform | Environment visually upgrades |
| achievement_unlock | Achievement notification |
| streak_bonus | Daily streak continues |

---

## 16. Localization (EN/AR)

### Implementation
- All user-facing strings stored in translation files
- Godot: CSV translation files (EN, AR columns)
- Django: JSON fields with `_en` and `_ar` suffixes on all content models
- RTL support for Arabic text rendering in Godot
- Arabic font: Noto Sans Arabic or Amiri (Google Fonts, free)

### Content Priority
- MVP: English only, Arabic structure in place
- Phase 2: Full Arabic translation of:
  - All UI strings
  - Personality assessment questions
  - Challenge content (all 8 realms)
  - Feed items
  - AI companion prompts

---

## 17. Security & Anti-Cheat

### API Security
| Measure | Implementation |
|---------|---------------|
| JWT Authentication | Short-lived access tokens (15 min), long refresh (7 days) |
| Rate Limiting | 60 req/min general, 10 req/min for AI companion |
| Request Validation | Serializer validation on all inputs |
| XP Validation | Server-side only — client never decides XP amounts |
| Challenge Validation | Server validates answers, client only displays |
| HTTPS Only | All API endpoints require HTTPS |
| CORS | Whitelist game client origins only |

### Anti-Cheat
- All game state authoritative on server
- Client sends answer data → server validates → server awards XP
- Time-based challenges validated server-side (started_at vs completed_at)
- Rate limit on challenge submissions (max 1 per 5 seconds)
- Anomaly detection: flag accounts with unrealistic stats

---

## 18. Monetization Implementation

### Free Tier
- Full access to Feed
- 3 daily quests
- 2 realm quests per day
- Basic companion chat (10 messages/day)
- View leaderboards
- Ads between challenges (non-intrusive)

### Premium Tier ($4.99/month or $39.99/year)
- Unlimited realm quests
- Unlimited companion chat
- No ads
- Detailed analytics dashboard
- Exclusive cosmetics
- Streak freeze (3/month)
- Priority feed content
- Early access to new realms

### Rewarded Ads
- Watch 30-sec ad → bonus XP (20% extra on next challenge)
- Watch ad → unlock 1 streak freeze
- Watch ad → get hint on challenge

---

## 19. Development Schedule (2-Week MVP)

### Day 1-2: Foundation
- [ ] Install Godot 4.3, set up project
- [ ] Set up Django project with all apps
- [ ] Database migrations
- [ ] JWT auth endpoints
- [ ] Basic Godot scene: main menu → hub world
- [ ] Player character with movement in empty world
- [ ] API client autoload in Godot

### Day 3-4: Assessment & Profile
- [ ] Assessment questions (30 items minimum)
- [ ] Assessment API (submit, score, store)
- [ ] Assessment UI in Godot (step-by-step flow)
- [ ] Profile API with radar chart data
- [ ] Profile screen in Godot with stat visualization

### Day 5-6: Hub World & Realms
- [ ] Hub world 3D environment (simple but atmospheric)
- [ ] 3 realm portals with visual state
- [ ] Logic Fortress environment (explorable)
- [ ] Emotion Ocean environment (explorable)
- [ ] Creativity Nebula environment (explorable)
- [ ] Portal transition effects

### Day 7-8: Challenge System
- [ ] Challenge models and API
- [ ] 5 Logic Fortress challenges (pattern, spatial, syllogism)
- [ ] 5 Emotion Ocean challenges (scenarios, emotion reading)
- [ ] 5 Creativity Nebula challenges (divergent thinking, story)
- [ ] Challenge UI overlay in Godot
- [ ] Challenge nodes in 3D world (interactable)

### Day 9-10: Progression & Companion
- [ ] XP system (award, track, level up)
- [ ] Stat progression (realm levels, visual stage calculation)
- [ ] Achievement system (10 initial achievements)
- [ ] Streak tracking
- [ ] Claude API integration for companion
- [ ] Companion chat UI in Godot
- [ ] Companion system prompt with player context

### Day 11-12: Feed & Polish
- [ ] Feed items (30-50 initial items across all types)
- [ ] Feed API with personalization
- [ ] Feed UI in Godot (scrollable cards)
- [ ] World transformation (Stage 0-2 visuals responding to stats)
- [ ] HUD (XP bar, level, current realm)
- [ ] Sound effects and ambient audio

### Day 13: Testing & Fixes
- [ ] End-to-end flow testing
- [ ] API error handling
- [ ] Mobile-responsive UI scaling
- [ ] Performance optimization (Godot web export)
- [ ] Bug fixes

### Day 14: Deploy & Launch
- [ ] Django deploy to Railway
- [ ] Godot web export → host on Vercel/Netlify/Railway static
- [ ] Android APK export (optional if time permits)
- [ ] Seed production database
- [ ] Final testing on live

---

## 20. Post-MVP Roadmap

### Phase 2 (Month 1-2 post-MVP)
- Remaining 5 realms (environments + challenges)
- Arena mode (async speed rounds, leaderboard)
- Arabic language support
- Android APK release
- Premium tier + payment integration (Stripe)
- 100+ additional challenges
- Advanced companion (proactive check-ins)

### Phase 3 (Month 3-4)
- Team battles (2v2)
- Clan/guild system
- Real-time arena matches
- iOS release
- Social features (friends, profiles)
- Video content in feed
- Seasonal events

### Phase 4 (Month 5-6)
- Desktop builds (Windows, Mac)
- Advanced analytics dashboard
- Community challenge creation (UGC)
- API for third-party integrations
- Performance optimization for scale

---

## 21. Questions for Review

### Game Design Questions
1. **Avatar style**: Should the player avatar be humanoid (stylized person) or abstract (geometric shape, light being)? This affects modeling cost.
2. **Challenge failure**: When a player gets a challenge wrong, should they be able to retry immediately, or must they wait (e.g., 30 min cooldown)?
3. **Difficulty adaptation**: Should challenge difficulty auto-adjust based on player performance (adaptive difficulty) or follow fixed quest progression?
4. **Companion name**: Should the AI companion have a fixed name, or should the player name it?
5. **Hub world navigation**: Should the player physically walk to portals, or can they also fast-travel via a menu?
6. **Challenge variety per quest**: Should each quest mix challenge types (e.g., 2 MCQ + 1 spatial + 1 scenario) or be a single type?
7. **Minimum session length**: What's the absolute minimum a player should be able to do in 1 minute? (e.g., 1 feed item + view stats?)

### Technical Questions
8. **Hosting the game client**: Where should the Godot web build be hosted? Same Railway instance, or separate static host (Vercel, Netlify)?
9. **Offline support**: Should the game work offline at all (cached challenges, local progress sync later)?
10. **Data export**: Should players be able to export/download their personality assessment and growth data?

### Content Questions
11. **Challenge tone**: Should challenges feel academic/educational, or more casual/conversational? Example: "Solve this syllogism" vs "Can you spot the flaw in this argument?"
12. **Cultural sensitivity**: Any topics to explicitly avoid or include for the 13-35 age range across cultures?
13. **Initial content volume**: For MVP, is 15 challenges + 30 feed items enough to test with, or do you want more depth even for prototype?

### Business Questions
14. **Name**: Is "MindArena" the final name, or should we brainstorm alternatives?
15. **Branding**: Any specific brand identity preferences (logo style, mascot, tagline)?
16. **Launch strategy**: Soft launch to a test group first, or public launch?

### Priority Questions
17. **If time gets tight in the 2-week sprint, what should we cut?** Suggested order of sacrifice:
    - Cut: Creativity Nebula realm (ship with 2 realms instead of 3)
    - Cut: Feed system (add post-MVP)
    - Cut: Sound/music (add post-MVP)
    - Cut: World transformation visuals (static worlds, add transformation later)
    - NEVER cut: Assessment, challenges, companion, progression — these are the core

18. **Should we start building tomorrow, or refine this plan further first?**
