# MindArena

A 3D gamified self-development universe where players explore 8 themed realms, complete cognitive and emotional challenges, and grow measurably through a personality-driven progression system.

**Target audience**: Ages 13-35
**Platforms**: Web (Godot HTML5 export), Android, Desktop

## Architecture

```
Godot 4.3 Game Client  ←→  Django 5.1 REST API  ←→  PostgreSQL 16 + Redis 7
        │                         │
    GDScript                 DRF + JWT Auth
    3D World                 Celery Workers
    UI Scenes                Claude API (AI Companion)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Game Engine | Godot 4.3 (GDScript) |
| Backend | Django 5.1 + Django REST Framework |
| Auth | JWT (SimpleJWT) |
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
│   │   ├── accounts/           # Player auth, profiles
│   │   ├── assessment/         # Personality assessment (Big Five + EQ)
│   │   ├── realms/             # 8 realms, quests, challenges
│   │   ├── progression/        # XP, levels, achievements, streaks
│   │   ├── companion/          # AI companion (Claude API)
│   │   ├── feed/               # Personalized content feed
│   │   ├── arena/              # PvP arena (Phase 2)
│   │   └── core/               # Pagination, permissions, exceptions
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── game/                       # Godot 4.3 game client
│   ├── project.godot
│   ├── scenes/                 # .tscn scene files
│   │   ├── main.tscn           # Entry point
│   │   ├── login.tscn          # Auth screen
│   │   ├── assessment.tscn     # Personality quiz
│   │   ├── world_hub.tscn      # Central hub with 8 realm portals
│   │   ├── challenge.tscn      # Challenge UI
│   │   ├── chat.tscn           # AI companion chat
│   │   ├── feed.tscn           # Content feed
│   │   ├── profile.tscn        # Player stats + radar chart
│   │   └── world/portal.tscn   # Reusable realm portal
│   ├── scripts/
│   │   ├── autoload/           # Singletons (6 autoloads)
│   │   ├── ui/                 # UI controllers
│   │   ├── player/             # Player movement
│   │   ├── world/              # Portal, world transformer
│   │   └── challenges/         # Challenge logic
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

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api/v1/accounts/register/` | POST | Create account |
| `api/v1/accounts/login/` | POST | Get JWT tokens |
| `api/v1/accounts/profile/` | GET | Player profile |
| `api/v1/assessment/questions/` | GET | Assessment questions |
| `api/v1/assessment/submit/` | POST | Submit assessment |
| `api/v1/realms/` | GET | List all realms |
| `api/v1/realms/{slug}/challenges/` | GET | Realm challenges |
| `api/v1/realms/challenges/{id}/submit/` | POST | Submit answer |
| `api/v1/progression/progression/stats/` | GET | Player stats |
| `api/v1/progression/achievements/earned/` | GET | Earned achievements |
| `api/v1/companion/chat/` | POST | Chat with AI companion |
| `api/v1/feed/` | GET | Personalized feed |

## XP System

- XP curve: `floor(100 * level^1.5)`
- 6 visual stages per realm (barren → mastery)
- Streak bonuses for daily activity
- 30+ achievements across categories

## Environment Variables

See `backend/.env.example` for the full list. Key variables:

- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `ANTHROPIC_API_KEY` — Claude API key for AI companion
