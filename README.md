# MindArena

A 3D gamified self-development universe where players explore 8 themed realms, complete cognitive and emotional challenges, compete in real-time arena battles, and grow measurably through a personality-driven progression system.

**Target audience**: Ages 13-35
**Platforms**: Web (Godot HTML5 export), Android, Desktop

## Architecture

```
Godot 4.3 Game Client  ←→  Django 5.1 REST API  ←→  PostgreSQL 16 + Redis 7
        │                         │
    GDScript                 DRF + JWT Auth
    3D World                 Celery Workers
    UI Scenes                Claude API (AI Companion)
    Arabic/English           ELO Matchmaking
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Game Engine | Godot 4.3 (GDScript) |
| Backend | Django 5.1 + Django REST Framework |
| Auth | JWT (SimpleJWT) with token rotation + blacklisting |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 + Celery 5.4 |
| AI Companion | Claude API (Anthropic) |
| Deployment | Docker Compose / Railway |

## Project Structure

```
MindArena/
├── backend/                    # Django REST API
│   ├── config/                 # Settings, URLs, WSGI, Celery
│   │   └── settings/           # base.py, development.py, production.py
│   ├── apps/
│   │   ├── accounts/           # Player auth, profiles, friends
│   │   ├── assessment/         # Personality assessment (Big Five + EQ)
│   │   ├── realms/             # 8 realms, quests, challenges
│   │   ├── progression/        # XP, levels, achievements, streaks
│   │   ├── companion/          # AI companion (Claude API)
│   │   ├── feed/               # Personalized content feed
│   │   ├── arena/              # PvP arena with ELO matchmaking
│   │   ├── notifications/      # In-app notification system
│   │   └── core/               # Pagination, permissions, throttles
│   ├── tests/                  # 53 integration tests
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── game/                       # Godot 4.3 game client
│   ├── project.godot
│   ├── scenes/                 # 9 .tscn scene files
│   │   ├── main.tscn           # Entry point
│   │   ├── login.tscn          # Auth screen
│   │   ├── assessment.tscn     # Personality quiz
│   │   ├── world_hub.tscn      # Central hub with 8 realm portals
│   │   ├── challenge.tscn      # Challenge UI
│   │   ├── chat.tscn           # AI companion chat
│   │   ├── feed.tscn           # Content feed
│   │   ├── profile.tscn        # Player stats + radar chart
│   │   └── world/portal.tscn   # Reusable realm portal
│   ├── scripts/                # 22 GDScript files
│   │   ├── autoload/           # 6 singletons (API, Auth, Player, Game, Scene, Audio)
│   │   ├── ui/                 # 10 UI controllers (incl. settings)
│   │   ├── player/             # Player controller with portal interaction
│   │   ├── world/              # Portal, world transformer
│   │   └── challenges/         # Challenge manager, MCQ logic
│   └── assets/                 # Theme, icons, textures
│
└── docker-compose.yml          # Full stack: DB + Redis + API + Celery
```

## The 8 Realms

| Realm | Focus | Color |
|-------|-------|-------|
| Logic Fortress | Logical reasoning, pattern matching | Blue |
| Emotion Ocean | Emotional intelligence, empathy | Teal |
| Creativity Nebula | Divergent thinking, imagination | Purple |
| Discipline Citadel | Habits, self-regulation, discipline | Gold |
| Knowledge Peaks | Memory, learning, knowledge | Green |
| Social Bridge | Social skills, communication | Orange |
| Wealth Garden | Financial literacy, planning | Emerald |
| Wellness Grove | Mindfulness, stress management | Pink |

## Game Flow

1. **Register/Login** → JWT authentication
2. **Personality Assessment** → 45-question Big Five + EQ assessment
3. **Enter World Hub** → 3D space with 8 glowing realm portals
4. **Walk to Portal** → Enter a realm (press E to interact)
5. **Complete Challenges** → MCQ, scenarios, creative prompts
6. **Earn XP** → Level up realms, unlock visual transformations
7. **Chat with Noor** → AI companion powered by Claude
8. **Browse Feed** → Personalized tips, puzzles, thought experiments
9. **Arena Battles** → Head-to-head challenge duels with ELO ranking
10. **Social** → Add friends, view leaderboards, compare progress

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Redis 7
- Godot Engine 4.3

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # Edit with your credentials
python manage.py migrate
python manage.py seed_game_content
python manage.py seed_achievements
python manage.py runserver
```

### Docker Setup

```bash
docker-compose up -d
# API available at http://localhost:8000
# Auto-runs migrations and seeds data
```

### Game Client

1. Open Godot Engine 4.3
2. Import Project → select `game/project.godot`
3. Press F5 to run

## API Endpoints

### Authentication
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/accounts/register/` | POST | Create account |
| `api/v1/accounts/login/` | POST | Get JWT tokens |
| `api/v1/accounts/token/refresh/` | POST | Refresh access token |
| `api/v1/accounts/profile/` | GET/PATCH | View/update profile |
| `api/v1/accounts/change-password/` | POST | Change password |
| `api/v1/accounts/delete-account/` | POST | Delete account |
| `api/v1/accounts/search/?q=` | GET | Search players |
| `api/v1/accounts/players/{id}/` | GET | Public player profile |

### Assessment
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/assessment/questions/` | GET | Get assessment questions |
| `api/v1/assessment/submit/` | POST | Submit assessment answers |
| `api/v1/assessment/result/` | GET | Get assessment results |

### Realms & Challenges
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/realms/` | GET | List all realms |
| `api/v1/realms/{slug}/` | GET | Realm detail |
| `api/v1/realms/{slug}/challenges/` | GET | Realm challenges |
| `api/v1/realms/challenges/{id}/` | GET | Challenge detail |
| `api/v1/realms/challenges/{id}/submit/` | POST | Submit answer |
| `api/v1/realms/quests/` | GET | List quests |
| `api/v1/realms/quests/{id}/start/` | POST | Start a quest |

### Progression
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/progression/stats/` | GET | Player progression stats |
| `api/v1/progression/history/` | GET | Challenge history |
| `api/v1/progression/achievements/` | GET | All achievements |
| `api/v1/progression/achievements/earned/` | GET | Earned achievements |
| `api/v1/progression/leaderboard/` | GET | Global/realm leaderboard |
| `api/v1/progression/daily-challenge/` | GET | Daily challenge per realm |

### Arena (PvP)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/arena/status/` | GET | Arena status and match types |
| `api/v1/arena/matches/` | GET | List matches (filter: ?status=waiting/mine) |
| `api/v1/arena/matches/create/` | POST | Create a new match |
| `api/v1/arena/matches/find/` | GET | Find open match (matchmaking) |
| `api/v1/arena/matches/{id}/` | GET | Match detail with participants |
| `api/v1/arena/matches/{id}/join/` | POST | Join a waiting match |
| `api/v1/arena/matches/{id}/challenge/` | GET | Current round's challenge |
| `api/v1/arena/submit/` | POST | Submit answer for current round |
| `api/v1/arena/stats/` | GET | Player's arena stats + ELO |
| `api/v1/arena/leaderboard/` | GET | Arena ELO leaderboard |

### Social
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/friends/` | GET | List friends |
| `api/v1/friends/request/` | POST | Send friend request |
| `api/v1/friends/requests/` | GET | Incoming friend requests |
| `api/v1/friends/respond/` | POST | Accept/reject friend request |
| `api/v1/friends/{player_id}/` | DELETE | Remove friend |

### Notifications
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/notifications/` | GET | List notifications (?unread_only=true) |
| `api/v1/notifications/mark-read/` | POST | Mark notifications as read |
| `api/v1/notifications/{id}/` | DELETE | Delete notification |

### AI Companion & Feed
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/companion/chat/` | POST | Chat with Noor (AI companion) |
| `api/v1/companion/history/` | GET | Conversation history |
| `api/v1/feed/` | GET | Personalized feed |
| `api/v1/feed/{id}/interact/` | POST | Like/complete feed item |

### Infrastructure
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/health/` | GET | Health check |

## Arena System

The Arena enables competitive head-to-head gameplay:

- **Match Types**: Speed Duel (2 players), Strategic Battle (2 players), Team Arena (4 players)
- **Matchmaking**: Create a match or find an open one via the find endpoint
- **Gameplay**: Both players answer the same challenges in each round
- **Scoring**: 100 points for correct answer + up to 50 time bonus points
- **ELO Rating**: Standard ELO system (K=32) updates after each match
- **Leaderboard**: Minimum 3 matches to appear on the leaderboard

## XP System

- XP curve: `floor(100 * level^1.5)`
- 6 visual stages per realm (barren → mastery)
- Streak bonuses for daily activity
- 30+ achievements across categories

## Bilingual Support

- All content supports English and Arabic (`_en`/`_ar` field suffixes)
- Player language preference stored in profile
- Godot UI controllers use `PlayerData.localized()` helper for dynamic language switching
- Settings screen allows runtime language toggle

## Security

- JWT with token rotation and blacklisting
- Rate limiting: 5/min on auth endpoints, 30/min anonymous, 120/min authenticated
- CORS configuration with explicit allowed headers
- HSTS, X-Frame-Options, Content-Type-Nosniff in production
- Password confirmation required for account deletion

## Testing

```bash
cd backend
python manage.py test tests --verbosity=2
```

53 integration tests covering: auth, registration, profiles, realms, challenges, assessment, feed, quests, progression, achievements, leaderboard, daily challenges, arena (create/join/play/finish), notifications, and friends.

## Celery Tasks

Background tasks managed by Celery:

| Task | Trigger | Purpose |
|------|---------|---------|
| `check_achievements_async` | After game events | Award achievements asynchronously |
| `update_daily_streak_async` | After any activity | Update player's daily streak |
| `recalculate_realm_levels` | After XP changes | Recalculate realm levels and visual stages |
| `cleanup_expired_tokens` | Daily at 3 AM UTC | Clean up expired JWT tokens |
| `generate_daily_stats` | Daily at 00:05 UTC | Log daily activity statistics |

## Challenge Types

| Type | Realms | Format |
|------|--------|--------|
| Multiple Choice | All | Question + 4 options |
| Pattern Match | Logic | Find the pattern, select answer |
| Sequence | Logic | Complete the sequence |
| Math Logic | Logic | Solve the problem |
| Timed Response | Logic | Speed-based answers |
| Scenario Choice | Emotion, Social, Discipline | Real-world scenarios |
| Creative Prompt | Creativity | Free-text creative response |
| Emotional Scenario | Emotion, Wellness | Empathy and regulation |
| Financial Decision | Wealth | Money management scenarios |

## Key Features

- **Personality-driven progression**: Assessment maps to 8 realm affinities
- **Visual world transformation**: Portals grow and glow as you level up (6 stages)
- **Achievement system**: 30+ achievements with automatic detection and XP rewards
- **AI Companion (Noor)**: Powered by Claude, adapts to your personality and language
- **Personalized feed**: Prioritizes content for your weakest realms
- **Arena PvP**: ELO-rated head-to-head challenges with matchmaking
- **Friend system**: Send requests, accept/reject, view friend profiles
- **Notification system**: Achievement, arena, friend, level-up, and system notifications
- **Bilingual**: Full Arabic and English support with runtime switching
- **JWT auth with auto-refresh**: Token rotation with blacklisting
- **Rate limiting**: Auth and API throttling with exponential backoff
- **Celery background tasks**: Async achievement checks, streak updates, periodic cleanup
- **API resilience**: Retry logic, connection status tracking, loading states in Godot

## Environment Variables

See `backend/.env.example` for the full list. Key variables:

- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `ANTHROPIC_API_KEY` — Claude API key for AI companion
- `DJANGO_ENV` — `development` (SQLite) or `production` (PostgreSQL)
