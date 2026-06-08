# 🎓 IFRI_MentorLink

Plateforme web de mentorat academique pour les etudiants de l'IFRI (Universite d'Abomey-Calavi).

## Fonctionnalites

- **Gestion des comptes** : inscription, connexion, reinitialisation mot de passe
- **Profils utilisateurs** : competences, disponibilites, filiere, photo
- **Algorithme de matching** : mise en correspondance mentor/mentore (competences + horaires + filiere)
- **Annonces** : publication et recherche d'offres/demandes de mentorat
- **Messagerie temps reel** : chat instantane via WebSocket (Socket.IO)
- **Notifications** : alertes en temps reel pour messages et matchs

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.11, Flask 3.0, Flask-SocketIO |
| BDD | PostgreSQL, SQLAlchemy ORM |
| Frontend | HTML5, CSS3, JavaScript ES6 |
| Auth | Flask-Login, Flask-Bcrypt |
| Temps reel | Flask-SocketIO, eventlet |

## Installation rapide

```bash
# 1. Cloner
git clone https://github.com/[GROUPE]/PIL1_2526_XX.git && cd PIL1_2526_XX

# 2. Environnement virtuel
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Base de donnees PostgreSQL
psql -U postgres -c "CREATE DATABASE mentorlink_db;"
psql -U postgres -c "CREATE USER mentorlink WITH PASSWORD 'mentorlink';"
psql -U postgres -c "GRANT ALL ON DATABASE mentorlink_db TO mentorlink;"
psql -U mentorlink -d mentorlink_db -f schema.sql

# 4. Variables d'environnement
echo "DATABASE_URL=postgresql://mentorlink:mentorlink@localhost/mentorlink_db" > .env
echo "SECRET_KEY=changez-moi" >> .env

# 5. Lancer
python run.py
```

Application disponible sur **http://localhost:5000**

## Structure

```
ifri_mentorlink/
├── run.py              # Entree principale
├── config.py           # Configuration
├── schema.sql          # Schema BDD
├── rapport.html        # Rapport de projet
├── requirements.txt
└── app/
    ├── models/         # Modeles SQLAlchemy
    ├── routes/         # Blueprints Flask
    ├── utils/          # Algorithme matching
    ├── templates/      # Templates Jinja2
    └── static/         # CSS, JS, uploads
```

## Equipe pedagogique

- **Supervision** : M. Ratheil HOUNDJI
- **Encadrants** : M. Armand ACCROMBESSI, Mme Maryse GAHOU
