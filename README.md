# CyberLearn — Jeu Intelligent

> Jeu narratif d'apprentissage de la cybersécurité — PEGI 18+
> Projet de stage PFE — Web4jobs — Master Ingénierie Logicielle

## Stack technique

| Composant | Technologie |
|---|---|
| Backend | FastAPI 0.111 + Python 3.11 |
| Frontend | Next.js 14 + React 18 + Tailwind CSS |
| Base de données | PostgreSQL 15 |
| Cache / Sessions | Redis 7 |
| IA Recommandation | scikit-learn (TF-IDF + cosine similarity) |
| Conteneurisation | Docker + Docker Compose |

## Démarrage rapide

### 1. Prérequis

- Docker Desktop installé et démarré
- Git

### 2. Cloner et configurer

```bash
git clone <repo>
cd cyberlearn

# Copier et remplir les variables d'environnement
cp .env.example .env
```

Éditer `.env` et remplir au minimum :
```env
POSTGRES_PASSWORD=votre_mot_de_passe_fort
REDIS_PASSWORD=votre_redis_password
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### 3. Démarrer le projet

```bash
docker compose up --build
```

### 4. Appliquer les migrations et insérer les données initiales

```bash
# Migrations
docker exec cyberlearn_api alembic upgrade head

# Données initiales (chapitres, missions, badges, compte admin)
docker exec cyberlearn_api python seed_data.py
```

### 5. Accéder à l'application

| Service | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **API Swagger** | http://localhost:8000/docs |
| **Service IA** | http://localhost:8001/health |

### Compte admin par défaut
- Email : `admin@cyberlearn.app`
- Mot de passe : `Admin!CyberLearn2025`

---

## Structure du projet

```
cyberlearn/
├── backend/                  # FastAPI Python 3.11
│   ├── app/
│   │   ├── main.py           # Point d'entrée
│   │   ├── core/             # Config, sécurité, exceptions, logging
│   │   ├── db/               # Database, Redis
│   │   ├── models/           # SQLAlchemy ORM
│   │   ├── schemas/          # Pydantic v2 DTO
│   │   ├── api/v1/           # Endpoints REST
│   │   └── services/         # Logique métier
│   ├── alembic/              # Migrations DB
│   ├── tests/                # Tests pytest
│   └── seed_data.py          # Données initiales
├── frontend/                 # Next.js 14 + React 18
│   └── src/
│       ├── app/              # Pages (App Router)
│       ├── components/       # Composants React
│       ├── lib/              # API client, Auth store
│       └── types/            # Types TypeScript
├── ai-service/               # Microservice IA (port 8001)
├── nginx/                    # Reverse proxy (production)
├── docker-compose.yml
└── .env.example
```

---

## Commandes utiles

```bash
# Démarrer en développement
docker compose up

# Logs d'un service
docker compose logs -f api
docker compose logs -f frontend

# Migrations
docker exec cyberlearn_api alembic upgrade head
docker exec cyberlearn_api alembic revision --autogenerate -m "description"

# Seed données
docker exec cyberlearn_api python seed_data.py

# Tests backend
docker exec cyberlearn_api pytest tests/ -v

# Shell PostgreSQL
docker exec -it cyberlearn_db psql -U cyberlearn_user -d cyberlearn

# Shell Redis
docker exec -it cyberlearn_redis redis-cli -a $REDIS_PASSWORD
```

---

## Endpoints API principaux

### Authentification
| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Inscription 18+ |
| POST | `/api/v1/auth/login` | Connexion |
| POST | `/api/v1/auth/logout` | Déconnexion |
| POST | `/api/v1/auth/refresh` | Renouvellement token |

### Jeu
| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/sessions/missions/{id}/start` | Démarrer mission |
| POST | `/api/v1/sessions/{id}/command` | Commande terminal |
| POST | `/api/v1/sessions/{id}/submit` | Soumettre solution |
| POST | `/api/v1/sessions/{id}/hint` | Demander indice |
| GET  | `/api/v1/sessions/{id}/results` | Résultats session |

### Catalogue et Progression
| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/catalogue/chapters` | Carte du jeu |
| GET | `/api/v1/catalogue/missions/{id}` | Fiche mission |
| GET | `/api/v1/progress/me` | Tableau de bord |
| GET | `/api/v1/progress/me/badges` | Badges obtenus |
| GET | `/api/v1/recommendations/me` | Recommandations IA |

---

## Sécurité

- ✅ Vérification âge 18+ double niveau (frontend Zod + backend Python)
- ✅ Mots de passe hachés bcrypt (coût 12)
- ✅ JWT access (1h) + refresh token HttpOnly cookie (7j)
- ✅ Solutions de missions hashées SHA-256 — jamais en clair côté client
- ✅ Rate limiting Redis : 5 tentatives login / 10 soumissions par session
- ✅ En-têtes HTTP sécurité (X-Frame-Options, CSP, HSTS)
- ✅ CORS restrictif sur origines autorisées uniquement

---

## Lancer les tests

```bash
docker exec cyberlearn_api pytest tests/ -v --tb=short
```

---

## Auteur

[Prénom NOM] — Stagiaire Master Ingénierie Logicielle
Web4jobs — 2025
