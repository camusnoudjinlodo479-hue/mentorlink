-- ============================================================
--  IFRI_MentorLink — Schéma de base de données
--  SGBD : MySQL / PostgreSQL
-- ============================================================

-- Suppression dans l'ordre inverse des dépendances
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS matching_results;
DROP TABLE IF EXISTS mentorship_requests;
DROP TABLE IF EXISTS user_availabilities;
DROP TABLE IF EXISTS user_skills;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS fields_of_study;

-- ============================================================
-- 1. Filières
-- ============================================================
CREATE TABLE fields_of_study (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20)  NOT NULL UNIQUE,
    label       VARCHAR(100) NOT NULL
);

INSERT INTO fields_of_study (code, label) VALUES
    ('IA',    'Intelligence Artificielle'),
    ('IM',    'Ingénierie Mathématique'),
    ('GL',    'Génie Logiciel'),
    ('SE',    'Systèmes Embarqués & IoT'),
    ('SI',    'Systèmes d''Information');

-- ============================================================
-- 2. Utilisateurs
-- ============================================================
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    phone           VARCHAR(20)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    field_id        INT          REFERENCES fields_of_study(id),
    study_level     VARCHAR(20)  NOT NULL DEFAULT 'L1'
                        CHECK (study_level IN ('L1','L2','L3','M1','M2')),
    bio             TEXT,
    photo_url       VARCHAR(500),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. Compétences / Matières
-- ============================================================
CREATE TABLE skills (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL UNIQUE,
    category    VARCHAR(100)
);

INSERT INTO skills (name, category) VALUES
    ('Algorithmique',           'Informatique fondamentale'),
    ('Python',                  'Programmation'),
    ('JavaScript',              'Programmation'),
    ('HTML/CSS',                'Développement web'),
    ('SQL',                     'Bases de données'),
    ('Bases de données',        'Bases de données'),
    ('Mathématiques discrètes', 'Mathématiques'),
    ('Algèbre linéaire',        'Mathématiques'),
    ('Probabilités',            'Mathématiques'),
    ('Machine Learning',        'IA'),
    ('Réseaux de neurones',     'IA'),
    ('Systèmes embarqués',      'Matériel'),
    ('IoT',                     'Matériel'),
    ('Génie logiciel',          'Méthodes'),
    ('Gestion de projet',       'Méthodes');

-- ============================================================
-- 4. Compétences des utilisateurs (points forts / faibles)
-- ============================================================
CREATE TABLE user_skills (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id    INT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    skill_type  VARCHAR(10) NOT NULL CHECK (skill_type IN ('strength','weakness')),
    level       SMALLINT DEFAULT 3 CHECK (level BETWEEN 1 AND 5),
    UNIQUE (user_id, skill_id, skill_type)
);

-- ============================================================
-- 5. Disponibilités horaires
-- ============================================================
CREATE TABLE user_availabilities (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
                -- 0=Lundi … 6=Dimanche
    start_time  TIME NOT NULL,
    end_time    TIME NOT NULL,
    CHECK (end_time > start_time)
);

-- ============================================================
-- 6. Offres & Demandes de mentorat
-- ============================================================
CREATE TABLE mentorship_requests (
    id              SERIAL PRIMARY KEY,
    author_id       INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_type    VARCHAR(10) NOT NULL CHECK (request_type IN ('offer','demand')),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    format          VARCHAR(10) NOT NULL DEFAULT 'both'
                        CHECK (format IN ('online','onsite','both')),
    status          VARCHAR(10) NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open','matched','closed')),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Compétences liées à une offre/demande
CREATE TABLE request_skills (
    request_id  INT NOT NULL REFERENCES mentorship_requests(id) ON DELETE CASCADE,
    skill_id    INT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (request_id, skill_id)
);

-- Disponibilités liées à une offre/demande
CREATE TABLE request_availabilities (
    id          SERIAL PRIMARY KEY,
    request_id  INT NOT NULL REFERENCES mentorship_requests(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time  TIME NOT NULL,
    end_time    TIME NOT NULL
);

-- ============================================================
-- 7. Résultats de matching
-- ============================================================
CREATE TABLE matching_results (
    id              SERIAL PRIMARY KEY,
    mentor_id       INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentee_id       INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score           NUMERIC(5,2) NOT NULL CHECK (score BETWEEN 0 AND 100),
    skill_score     NUMERIC(5,2),
    schedule_score  NUMERIC(5,2),
    field_score     NUMERIC(5,2),
    status          VARCHAR(10) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','accepted','rejected')),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (mentor_id, mentee_id)
);

-- ============================================================
-- 8. Conversations & Messages
-- ============================================================
CREATE TABLE conversations (
    id          SERIAL PRIMARY KEY,
    user1_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (user1_id <> user2_id),
    UNIQUE (user1_id, user2_id)
);

CREATE TABLE messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INT     NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id       INT     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content         TEXT    NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 9. Notifications
-- ============================================================
CREATE TABLE notifications (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type        VARCHAR(50) NOT NULL,
    content     TEXT NOT NULL,
    is_read     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Index pour les performances
-- ============================================================
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_sender       ON messages(sender_id);
CREATE INDEX idx_notif_user            ON notifications(user_id);
CREATE INDEX idx_matching_mentor       ON matching_results(mentor_id);
CREATE INDEX idx_matching_mentee       ON matching_results(mentee_id);
CREATE INDEX idx_user_skills_user      ON user_skills(user_id);
CREATE INDEX idx_requests_author       ON mentorship_requests(author_id);
