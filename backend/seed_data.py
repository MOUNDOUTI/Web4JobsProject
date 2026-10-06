"""
CyberLearn — Script de seed
Insère les chapitres, missions et badges initiaux en base de données.
Commande : docker exec cyberlearn_api python seed_data.py
"""

import asyncio
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.badge import Badge, BadgeCondition
from app.models.chapter import Chapter
from app.models.mission import DifficultyLevel, Mission, MissionType
from app.models.user import User, UserRole


def sha256(s: str) -> str:
    return hashlib.sha256(s.strip().lower().encode()).hexdigest()


async def seed():
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with SessionLocal() as db:
        # ── Compte admin ──────────────────────────────────────────────────────
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.email == "admin@cyberlearn.app"))
        if not existing.scalar_one_or_none():
            admin = User(
                email="admin@cyberlearn.app",
                pseudo="CyberAdmin",
                password_hash=hash_password("Admin!CyberLearn2025"),
                birth_date="1990-01-01",
                is_verified_18=True,
                role=UserRole.admin,
                total_xp=0,
                level=1,
            )
            db.add(admin)
            print("✅ Compte admin créé : admin@cyberlearn.app / Admin!CyberLearn2025")

        # ── Chapitre 1 ────────────────────────────────────────────────────────
        ch1 = Chapter(
            title="L'Alerte Initiale",
            order_num=1,
            description="Votre première mission en tant qu'agent CSDF. Découvrez les bases de la cybersécurité.",
            narrative_context="Le siège de la CSDF. Sarah Malik vous accueille et vous brief sur votre première mission.",
            unlock_level=1,
        )
        db.add(ch1)
        await db.flush()

        # Mission 1-1 : Quiz de bienvenue
        m1_1 = Mission(
            chapter_id=ch1.id,
            title="Bienvenue à la CSDF",
            order_num=1,
            mission_type=MissionType.quiz,
            difficulty=DifficultyLevel.beginner,
            description="Testez vos connaissances de base en cybersécurité pour intégrer la CSDF.",
            narrative_intro="Sarah vous tend un tablet : 'Avant de vous confier une mission, nous devons évaluer votre niveau. Répondez à ces questions.'",
            narrative_outro="Excellent ! Vous avez prouvé vos connaissances de base. Sarah sourit : 'Bienvenue dans l'équipe, Agent Chen.'",
            skills_targeted=["bases cybersécurité", "vocabulaire"],
            xp_reward=20,
            time_limit_seconds=600,
            config={
                "questions": [
                    {
                        "text": "Qu'est-ce qu'un pare-feu (firewall) ?",
                        "options": [
                            "Un antivirus",
                            "Un système filtrant le trafic réseau",
                            "Un mot de passe complexe",
                            "Un type de malware"
                        ],
                        "correct": 1,
                        "explanation": "Un pare-feu filtre le trafic réseau entrant et sortant selon des règles définies."
                    },
                    {
                        "text": "Que signifie HTTPS ?",
                        "options": [
                            "HyperText Transfer Protocol Secure",
                            "High Transfer Text Protocol System",
                            "HyperText Transfer Private System",
                            "Hyper Transfer Text Protocol Safe"
                        ],
                        "correct": 0,
                        "explanation": "HTTPS = HTTP + TLS/SSL. Le 'S' signifie Secure — les données sont chiffrées."
                    },
                    {
                        "text": "Quel est le risque n°1 de l'OWASP Top 10 2021 ?",
                        "options": [
                            "Injection SQL",
                            "Cross-Site Scripting (XSS)",
                            "Broken Access Control",
                            "Cryptographic Failures"
                        ],
                        "correct": 2,
                        "explanation": "Depuis 2021, 'Broken Access Control' est en tête de l'OWASP Top 10."
                    },
                    {
                        "text": "Qu'est-ce qu'un hash MD5 ?",
                        "options": [
                            "Un algorithme de chiffrement symétrique",
                            "Une fonction de hachage cryptographique",
                            "Un protocole réseau",
                            "Un type de certificat SSL"
                        ],
                        "correct": 1,
                        "explanation": "MD5 est une fonction de hachage qui produit une empreinte de 128 bits. Considéré comme non sécurisé aujourd'hui."
                    },
                    {
                        "text": "Que signifie 'phishing' ?",
                        "options": [
                            "Une attaque par déni de service",
                            "Un logiciel malveillant",
                            "Une tentative d'hameçonnage par usurpation d'identité",
                            "Un type d'injection SQL"
                        ],
                        "correct": 2,
                        "explanation": "Le phishing consiste à se faire passer pour une entité de confiance pour voler des informations."
                    },
                ],
                "time_per_question": 30,
                "shuffle_questions": True,
                "solution_hash": sha256("completed"),
            },
        )
        db.add(m1_1)

        # Mission 1-2 : Email suspect
        m1_2 = Mission(
            chapter_id=ch1.id,
            title="L'Email Suspect",
            order_num=2,
            mission_type=MissionType.log_analysis,
            difficulty=DifficultyLevel.beginner,
            description="Analysez un email suspect et identifiez les indices de phishing.",
            narrative_intro="Victor vous envoie un message : 'On a intercepté cet email sur le réseau d'AtlasCo. Analysez-le et trouvez le flag caché dans les métadonnées.'",
            narrative_outro="Bien joué ! Vous avez identifié le phishing. L'email venait de phisher@fake-atlasco.com — le domaine était usurpé.",
            skills_targeted=["phishing", "analyse email", "social engineering"],
            xp_reward=25,
            time_limit_seconds=900,
            config={
                "terminal_commands": {
                    "ls": "emails/  tools/  README.txt",
                    "cat README.txt": "Analysez l'email suspect dans emails/. Utilisez les outils disponibles.",
                    "ls emails/": "suspicious_email.eml  metadata.txt",
                    "cat emails/suspicious_email.eml": (
                        "From: support@atlasco-security.com\n"
                        "To: employees@atlasco.com\n"
                        "Subject: [URGENT] Réinitialisation de mot de passe requise\n"
                        "Date: Mon, 14 Sep 2026 09:23:11 +0200\n\n"
                        "Cher(e) employé(e),\n\n"
                        "Votre compte a été compromis. Cliquez ICI pour réinitialiser votre mot de passe :\n"
                        "http://atlasco-security.com.fake-login.ru/reset\n\n"
                        "Cordialement,\nL'équipe Sécurité AtlasCo"
                    ),
                    "cat emails/metadata.txt": (
                        "Return-Path: phisher@fake-atlasco.com\n"
                        "X-Originating-IP: 185.220.101.47\n"
                        "Received-SPF: FAIL\n"
                        "DKIM: FAIL\n"
                        "Clue: Le flag est le domaine réel de l'expéditeur sans l'extension"
                    ),
                    "ls tools/": "header_analyzer  link_checker  spf_check",
                    "tools/spf_check suspicious_email.eml": "SPF: FAIL — Le domaine expéditeur ne correspond pas à l'IP source",
                    "tools/link_checker suspicious_email.eml": "URL suspecte détectée : .ru domain + sous-domaine trompeur",
                    "tools/header_analyzer suspicious_email.eml": "Return-Path réel : phisher@fake-atlasco.com\nDifférent de l'adresse affichée !",
                    "whoami": "agent_chen@csdf.gov",
                    "help": "Commandes : ls, cat, tools/header_analyzer, tools/link_checker, tools/spf_check",
                },
                "solution_hash": sha256("fake-atlasco"),
                "hints": [
                    "Regardez les métadonnées de l'email avec 'cat emails/metadata.txt'",
                    "Utilisez tools/header_analyzer pour analyser les en-têtes",
                    "Le flag est le domaine de l'adresse Return-Path sans l'extension .com",
                ],
            },
        )
        db.add(m1_2)

        # Mission 1-3 : Mot de passe faible
        m1_3 = Mission(
            chapter_id=ch1.id,
            title="Le Mot de Passe Faible",
            order_num=3,
            mission_type=MissionType.terminal,
            difficulty=DifficultyLevel.beginner,
            description="Découvrez pourquoi les mots de passe faibles sont dangereux en simulant une attaque par dictionnaire.",
            narrative_intro="Sarah : 'Un compte admin d'AtlasCo utilise un mot de passe dans notre dictionnaire des 1000 pires mots de passe. Trouvez-le.'",
            narrative_outro="Le mot de passe 'password123' était dans le top 10 des mots de passe les plus utilisés. Toujours utiliser des mots de passe complexes !",
            skills_targeted=["mots de passe", "attaque dictionnaire", "hachage"],
            xp_reward=30,
            time_limit_seconds=1200,
            config={
                "terminal_commands": {
                    "ls": "hashes.txt  wordlist.txt  tools/  README.txt",
                    "cat README.txt": "Trouvez le mot de passe de l'admin en analysant le hash MD5 fourni.",
                    "cat hashes.txt": "admin_hash: 482c811da5d5b4bc6d497ffa98491e38",
                    "cat wordlist.txt": "123456\npassword\npassword123\nqwerty\nabc123\nletmein\n[... 994 autres entrées ...]",
                    "tools/md5crack hashes.txt wordlist.txt": "[*] Tentative en cours...\n[+] Hash trouvé !\n[+] 482c811da5d5b4bc6d497ffa98491e38 = ?\n[!] Utilisez 'tools/md5crack --show' pour révéler",
                    "tools/md5crack --show": "482c811da5d5b4bc6d497ffa98491e38:password123\n[!] FLAG : Le mot de passe est 'password123'",
                    "tools/md5crack --help": "Usage: tools/md5crack <hashfile> <wordlist>\nOptions: --show (révéler résultats), --help",
                    "help": "Commandes disponibles : ls, cat, tools/md5crack",
                },
                "solution_hash": sha256("password123"),
                "hints": [
                    "Regardez le fichier hashes.txt pour obtenir le hash MD5 à cracker",
                    "Utilisez tools/md5crack avec le hash et la wordlist",
                    "Utilisez 'tools/md5crack --show' après l'analyse",
                ],
            },
        )
        db.add(m1_3)

        # ── Chapitre 2 ────────────────────────────────────────────────────────
        ch2 = Chapter(
            title="Infiltration",
            order_num=2,
            description="Plongez dans les techniques d'injection SQL et d'exploitation de failles web.",
            narrative_context="Les serveurs d'AtlasCo semblent vulnérables. Victor vous brief sur les techniques d'injection SQL.",
            unlock_level=2,
        )
        db.add(ch2)
        await db.flush()

        m2_1 = Mission(
            chapter_id=ch2.id,
            title="Le Formulaire Vulnérable",
            order_num=1,
            mission_type=MissionType.terminal,
            difficulty=DifficultyLevel.beginner,
            description="Exploitez une injection SQL basique dans un formulaire de connexion fictif.",
            narrative_intro="Victor : 'Le portail RH d'AtlasCo utilise une requête SQL non protégée. Accédez au compte admin sans connaître le mot de passe.'",
            narrative_outro="Vous avez réussi le bypass SQL ! La requête originale était : SELECT * FROM users WHERE user='' OR '1'='1'-- AND pass=''",
            skills_targeted=["injection SQL", "bypass authentification", "OWASP A03"],
            xp_reward=40,
            time_limit_seconds=1500,
            config={
                "terminal_commands": {
                    "ls": "target/  tools/  notes.txt",
                    "cat notes.txt": "Cible : http://hr.atlasco.local/login\nObjectif : Accéder au compte admin via SQLi",
                    "tools/sqltest --url hr.atlasco.local/login": "[*] Test d'injection SQL...\n[+] Paramètre 'username' vulnérable !\n[+] Type : Boolean-based blind SQLi\n[!] Essayez un payload dans le champ username",
                    "tools/sqltest --payload \"' OR '1'='1'--\" --url hr.atlasco.local/login": (
                        "[*] Envoi du payload...\n"
                        "[+] Authentification bypassée !\n"
                        "[+] Connecté en tant que : admin\n"
                        "[+] Session token : FLAG{SQL_Byp4ss_1nj3ct10n}\n"
                        "[!] Données accessibles : 47 employés, données RH confidentielles"
                    ),
                    "tools/sqltest --help": "Usage: tools/sqltest --url <target> [--payload <sqli>]\nExemple payload : ' OR '1'='1'--",
                    "cat target/login_form.html": "<form>\n  Username: <input name='username'>\n  Password: <input name='password'>\n  Requête: SELECT * FROM users WHERE user='$user' AND pass='$pass'\n</form>",
                    "help": "Commandes : ls, cat, tools/sqltest",
                },
                "solution_hash": sha256("FLAG{SQL_Byp4ss_1nj3ct10n}"),
                "hints": [
                    "Utilisez tools/sqltest pour analyser la cible",
                    "Essayez tools/sqltest avec le paramètre --payload",
                    "Le payload classique est : ' OR '1'='1'--",
                ],
            },
        )
        db.add(m2_1)

        # ── Badges ────────────────────────────────────────────────────────────
        badges = [
            Badge(
                name="Première Mission",
                description="Complétez votre première mission CyberLearn.",
                condition_type=BadgeCondition.first_mission,
                condition_value=1,
                icon_url="/static/badges/first_mission.png",
            ),
            Badge(
                name="Analyste Débutant",
                description="Complétez 5 missions.",
                condition_type=BadgeCondition.mission_count,
                condition_value=5,
                icon_url="/static/badges/analyst.png",
            ),
            Badge(
                name="Chasseur de Flags",
                description="Complétez 10 missions.",
                condition_type=BadgeCondition.mission_count,
                condition_value=10,
                icon_url="/static/badges/hunter.png",
            ),
            Badge(
                name="Chapitre 1 Complété",
                description="Terminez toutes les missions du Chapitre 1.",
                condition_type=BadgeCondition.chapter_complete,
                condition_value=1,
                condition_chapter_id=ch1.id,
                icon_url="/static/badges/chapter1.png",
            ),
            Badge(
                name="Marathonien",
                description="Accumulez 500 XP.",
                condition_type=BadgeCondition.xp_total,
                condition_value=500,
                icon_url="/static/badges/marathon.png",
            ),
            Badge(
                name="Perfectionniste",
                description="Obtenez un score parfait sur 3 missions.",
                condition_type=BadgeCondition.perfect_score,
                condition_value=3,
                icon_url="/static/badges/perfect.png",
            ),
            Badge(
                name="Sans Indice",
                description="Complétez 5 missions sans utiliser d'indice.",
                condition_type=BadgeCondition.no_hint,
                condition_value=5,
                icon_url="/static/badges/no_hint.png",
            ),
        ]
        for badge in badges:
            db.add(badge)

        await db.commit()
        print("✅ Seed terminé avec succès !")
        print(f"   - 2 chapitres créés")
        print(f"   - 4 missions créées (Ch1: 3 missions, Ch2: 1 mission)")
        print(f"   - {len(badges)} badges créés")
        print(f"   - Compte admin : admin@cyberlearn.app / Admin!CyberLearn2025")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
