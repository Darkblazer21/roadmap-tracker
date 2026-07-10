# Parcours 12–14 mois → Backend / Cloud Engineer Remote (2500–5000 $/mois)
**Objectif** : Devenir ingénieur backend/cloud remote international depuis Dakar
**Stack cible** : Python • FastAPI • PostgreSQL • Docker • AWS • Redis • React minimal • Wave/Stripe
**Salaire visé** : 2500–3500 $ (6 premiers mois) → 3500–5000 $ (après 1 an d'expérience client)

Avantage Sénégal : Intégration paiement **Wave réel** + connaissance marché local = énorme différenciant sur Toptal/Andela/Upwork

## Principes du parcours
- Project-based : 2 gros projets déployés (Discord-like + SaaS immobilier)
- Portfolio & README **en anglais** dès le début
- Certifications : **AWS SAA-C03 d'abord** → AWS Developer Associate optionnel ensuite
- Rythme conseillé : 15–25 h/semaine (2–4 h/j en semaine + 5–8 h week-end)
- Tracker : Notion / Trello + récap chaque dimanche soir
- Un repo GitHub public dès la semaine 1, même petit (les recruteurs regardent la régularité des commits)
- 1h d'anglais technique/semaine intégrée au plan (shadowing de talks, podcasts tech)

## Timeline globale (52–56 semaines)

### Mois 1–1.5 – Python solide (Semaines 1–6)
| Semaine | Thème principal                        | Ressources principales                              | Livrable dimanche soir                              | Heures estim. |
|---------|----------------------------------------|-----------------------------------------------------|-----------------------------------------------------|---------------|
| 1       | Bases absolues                         | Python Crash Course (chap. 1–5)                     | Script IMC + convertisseur XOF→USD                  | 12–16 h       |
| 2       | Fonctions, fichiers, exceptions        | Crash Course chap. 6–8 + 10                         | Lecture CSV factures + calcul total                 | 14–18 h       |
| 3       | Dictionnaires, modules, JSON, regex    | Crash Course chap. 9 + json + module re (regex)     | Gestion contacts JSON + recherche + validation email/tel par regex | 15–19 h |
| 4       | OOP basics                             | Crash Course chap. 9 + Effective Python : Chapitre 7 – Classes and Interfaces (items 48–57) | Classe Produit + Panier (ajout/total/réduction)     | 15–20 h       |
| 5       | Bonnes pratiques + typing + décorateurs| Effective Python : Chapitre 1 – Pythonic Thinking (items 1–9), Chapitre 5 – Functions (items 30–39, dont décorateurs item 38) + Item 124 (typing) + mypy intro | Refactor scripts précédents avec type hints + un décorateur perso (ex. chrono d'exécution) | 16–20 h |
| 6       | Async basics + Automatisation + mini-projet | realpython.com "Async IO in Python" (bases async/await) + smtplib / requests / python-telegram-bot | Bot Telegram prix devises + alerte email            | 18–24 h       |

> 🔧 Ajout : en parallèle des semaines 1–3, refaire les 2 premières semaines du MOOC Python de l'Université d'Helsinki (déjà entamé) — bon complément pratique à Crash Course, notamment sur les regex et les structures de données, sans bloc horaire séparé (à absorber dans les heures déjà prévues).
> 🔧 Ajout : la session async basics + décorateurs (semaines 5–6) comble un vrai trou du plan initial — c'est ce qui manquait pour aborder sereinement python-telegram-bot (une librairie asynchrone qui utilise des décorateurs pour déclarer ses handlers).

### Mois 2 – FastAPI & Backend moderne (Semaines 7–10)
| Semaine | Focus                                  | Ressources clés                                     | Livrable                                            | Heures   |
|---------|----------------------------------------|-----------------------------------------------------|-----------------------------------------------------|----------|
| 7       | FastAPI intro + Pydantic               | fastapi.tiangolo.com/tutorial (sections 1–10)       | API CRUD tâches (in-memory)                         | 15–20 h  |
| 8       | Path/Query/Body + validation           | Tutorial → Path / Query / Request Body              | API films/séries + filtres                          | 16–22 h  |
| 9       | SQLAlchemy async + PostgreSQL          | Tutorial → SQL Databases + async-sql-databases      | API users + todos en Postgres                       | 18–24 h  |
| 10      | JWT Auth + Pytest                      | Tutorial → Security OAuth2 + Pytest docs            | API protégée JWT + ≥12 tests                        | 18–25 h  |

### Mois 3–5 – Projet 1 : Discord-like mini scalable (Semaines 11–22)
Objectif : Chat textuel multi-room, WebSockets scalables via Redis

| Semaine | Focus                                        | Ressources / étapes                                      | Livrable principal                                      | Heures   |
|---------|----------------------------------------------|----------------------------------------------------------|---------------------------------------------------------|----------|
| 11–12   | Structure + auth + models servers/users      | Code semaine 10 + tables servers/members                 | Auth JWT + création servers & users                     | 20–26 h  |
| 13–14   | Channels + messages CRUD                     | FastAPI + SQLAlchemy async                               | CRUD channels + messages par channel                    | 20–26 h  |
| 15–16   | WebSockets basiques                          | fastapi.tiangolo.com/advanced/websockets                 | Chat simple (broadcast room)                            | 18–24 h  |
| 17–18   | Scaling avec Redis Pub/Sub                   | oneuptime.com/blog/.../websocket-servers-fastapi-redis   | Chat multi-room scalable Redis                          | 20–28 h  |
| 19–20   | Frontend React minimal + WS                  | freeCodeCamp React 2025/26 + Tailwind basics (séparés)   | UI servers/channels + chat temps réel                   | 22–30 h  |
| 21–22   | Docker + déploiement AWS EC2                 | Docker docs + tuto "FastAPI Docker AWS EC2 2026"         | App live + README anglais + screenshots                 | 22–32 h  |

> ⚠️ Semaines 19–22 denses : prévoir un buffer d'1–2 semaines si besoin. Apprendre React et Tailwind séparément avant de les combiner.

### Mois 5–7 – Projet 2 : SaaS Immobilier Sénégal (Semaines 23–34)
Paiement Wave réel + Stripe test + photos S3

| Semaine | Focus                                        | Ressources / étapes                                      | Livrable                                                | Heures   |
|---------|----------------------------------------------|----------------------------------------------------------|---------------------------------------------------------|----------|
| 23–24   | Modèles + CRUD annonces/users/favoris        | Stack projet 1                                           | Backend annonces + filtres (prix/zone/type)             | 20–26 h  |
| 25–26   | Auth + rôles (proprio/locataire/admin)       | FastAPI dependencies + JWT roles                         | Inscription/login + dashboard proprio                   | 18–24 h  |
| 27–28   | Frontend React + Tailwind + recherche        | Tailwind docs + React Router                             | Liste annonces + détail + formulaire recherche          | 22–30 h  |
| 29–30   | Paiement Wave Checkout + Stripe test         | docs.wave.com/checkout + Stripe test mode                | Paiement réservation Wave + fallback Stripe             | 20–28 h  |
| 31–32   | Upload images → AWS S3                       | FastAPI UploadFile + boto3                               | Upload & affichage photos depuis S3                     | 18–24 h  |
| 33–34   | Docker Compose + déploiement EC2/RDS/S3      | Docker Compose + tuto AWS FastAPI RDS S3                 | SaaS live (DuckDNS/Cloudflare) + README complet         | 25–35 h  |

> ⚠️ Semaines 33–34 denses : prévoir un buffer d'1–2 semaines si besoin.

### Mois 8 – DevOps & infra light (Semaines 35–38)
| Semaine | Focus                                        | Ressources                                               | Livrable                                                | Heures   |
|---------|----------------------------------------------|----------------------------------------------------------|---------------------------------------------------------|----------|
| 35      | Docker avancé + Compose multi-services       | Docker docs + Compose tutorial                           | docker-compose complet SaaS                             | 16–22 h  |
| 36      | GitHub Actions CI/CD                         | GitHub Actions docs + tuto FastAPI CI/CD                 | Pipeline test + build + deploy auto                     | 18–24 h  |
| 37      | Terraform basics (IaC)                       | HashiCorp Learn AWS (EC2 + S3)                           | .tf pour EC2 + S3 du projet                             | 18–25 h  |
| 38      | Monitoring simple + structlog                | AWS CloudWatch + structlog                               | Logs structurés + alerte CPU/mem                        | 15–20 h  |

> À partir de la semaine 35 : lire System Design Primer (2h/semaine max, sections 1–6 uniquement) en parallèle — pas en bloc séparé.

### Mois 9–10 – Certifications (Semaines 39–48)
| Semaine | Focus                        | Ressources principales                                   | Objectif / livrable                          | Heures/sem |
|---------|------------------------------|----------------------------------------------------------|----------------------------------------------|------------|
| 39–42   | AWS SAA-C03                  | Udemy Stephane Maarek SAA-C03 2026                       | Labs + 2 examens blancs >80%                 | 20–28 h    |
| 43      | Passage AWS SAA-C03          | AWS free tier + practice exams                           | Certification obtenue                        | —          |
| 44–47   | Projet 3 (perso) : agent de veille emploi + matching IA | APIs légitimes de job boards (RemoteOK, Arbeitnow, Adzuna, etc.) + agent orchestré sur VPS + notifications email/Telegram | Outil perso fonctionnel : agrégation offres → matching IA sur ton profil → notification avec validation manuelle avant candidature | 18–25 h |
| 44–47   | Kubernetes basics (optionnel, si temps restant)| KodeKloud "Kubernetes for Beginners" ou équivalent       | Pods, services, déploiements de base         | 10–15 h    |
| 48      | Révision + préparation hunt  | Relecture projets + GitHub + LinkedIn                    | Profil à jour, repos propres                 | 20–26 h    |

> CCNA supprimé : hors cible pour backend/cloud remote.
> Projet 3 (agent de veille emploi) : priorité sur Kubernetes basics en semaines 44–47, car il sert directement le job hunt qui suit (semaines 49+) et démontre une vraie compétence d'orchestration d'agents IA — un vrai différenciant dans le contexte 2026. Utilise des sources légitimes (APIs publiques de job boards) plutôt que du scraping LinkedIn, qui viole ses CGU et expose ton compte (et ceux d'éventuels futurs utilisateurs) à un bannissement. Kubernetes basics devient optionnel/allégé, à faire seulement s'il reste du temps.
> Monétisation (offre payante ~1000 FCFA/mois) : à envisager seulement après ton premier contrat remote signé — pas avant. Garde-le en usage perso pendant le job hunt, le temps de valider l'outil et de sécuriser tes propres revenus.
> AWS Developer Associate : optionnel, à faire uniquement si AWS SAA-C03 est obtenu et qu'il reste du temps avant le job hunt.

### Mois 11–13 – Portfolio & Job Hunt (Semaines 49–56+)
| Semaine | Actions clés                             | Détails                                                                 | Livrable                                          | Heures/sem |
|---------|------------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------|------------|
| 49–50   | READMEs & portfolio anglais              | README pro + diagrammes draw.io + GitHub Pages                          | 2 repos impeccables + mini-site portfolio         | 15–22 h    |
| 50–52   | System Design prep + entretiens          | Gaurav Sen playlist (load balancing, caching, WebSockets, queues) + System Design Primer sections 1–6 | Prêt pour questions system design basiques | 8–12 h    |
| 51      | LinkedIn + CV remote                     | Headline : "Python Backend \| FastAPI, AWS \| Dakar" + photo pro        | Profil + CV 1 page anglais                        | 12–18 h    |
| 52–54   | Candidatures + activation monitoring     | Toptal, Andela, Upwork, Arc.dev, Contra, RemoteOK, LinkedIn, Wellfound + ton Projet 3 pour le suivi | 8–12 candidatures qualitatives/sem + tracking + alertes auto sur réponses recruteurs/entretiens via ton agent | 15–25 h |
| 55+     | Entretiens + itérations                  | LeetCode easy/medium (incl. programmation dynamique : memoization, tableaux DP) + system design simple + features bonus projets | Premier contrat remote signé                      | variable   |

> Candidatures : privilégier 8–12 candidatures qualitatives par semaine plutôt que 15–30 en masse.
> À partir de la semaine 52, ton Projet 3 prend son rôle complet : suivi des réponses recruteurs et alarme dès qu'une offre ou un entretien sérieux arrive, en plus du matching fait en amont.

## Conseils finaux
- **Anglais** : README + LinkedIn + pitchs → en anglais dès maintenant. 1h/semaine de shadowing ou podcasts tech en anglais
- **GitHub public** : premier repo dès la semaine 1, commits réguliers — les recruteurs regardent l'historique
- **Avantage local** : mets en avant **Wave paiement réel** + compréhension marché Sénégal — c'est un différenciant fort sur Toptal/Andela
- **Dimanche soir** : commit + récap 3 lignes (succès / blocages / prochaine étape)
- **Si tu coinces** : demande la semaine précise (ex. "semaine 17 Redis pub/sub")
- **Certifications** : AWS SAA-C03 obligatoire → Kubernetes basics utile → AWS Developer Associate optionnel → CCNA inutile pour cet objectif
- **System Design** : Gaurav Sen playlist + sections 1–6 du Primer suffisent pour Toptal/Andela. Pas de bloc séparé, en parallèle semaines 35–52 uniquement
- **learntocloud.guide** : à ignorer — tout ce qu'il couvre est déjà dans ce plan, souvent mieux

Bonne chance Kingbrems ! 🚀
Tu as tout pour cartonner depuis Dakar.

---
*Modifications apportées par rapport à la version initiale :*
- *CCNA supprimé → remplacé par Kubernetes basics (semaines 44–47)*
- *AWS Developer Associate déplacé en optionnel*
- *System Design Primer intégré en parallèle (semaines 35–52, 2h/sem) plutôt qu'en bloc*
- *Gaurav Sen playlist ajoutée en semaines 50–52 pour prep entretiens*
- *Candidatures : 8–12 qualitatives/sem au lieu de 15–30*
- *Repo GitHub public dès semaine 1 ajouté aux principes*
- *1h anglais technique/semaine ajoutée aux principes*
- *Buffers signalés sur semaines 19–22 et 33–34*
- *learntocloud.guide explicitement déconseillé dans les conseils finaux*

*Modifications version 2 (juillet 2026) :*
- *Références Effective Python corrigées sur la 3e édition réelle (semaines 4 et 5 : chapitres et items exacts)*
- *Regex ajoutées en semaine 3 (module re)*
- *Décorateurs ajoutés en semaine 5 (Effective Python item 38 + exercice perso)*
- *Bases async/await ajoutées en semaine 6, avant le projet Bot Telegram (combler le trou identifié avec python-telegram-bot)*
- *MOOC Python Helsinki (2 premières semaines) ajouté en complément parallèle des semaines 1–3*
- *Projet 3 ajouté : agent de veille emploi + matching IA (semaines 44–47), prioritaire sur Kubernetes basics qui devient optionnel/allégé*
- *Précision : sources légitimes (APIs job boards) à utiliser pour le Projet 3, pas de scraping LinkedIn (risque CGU/bannissement)*
- *Monétisation du Projet 3 repoussée après le premier contrat signé*
- *Monitoring des réponses recruteurs + alertes entretien via le Projet 3 intégrés semaines 52+*
- *Programmation dynamique (memoization, tableaux DP) précisée dans la prep LeetCode semaine 55+*