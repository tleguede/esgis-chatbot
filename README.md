# ESGIS Chatbot

Projet scolaire Python : ChatBot connecté à l’IA Mistral, persistance DynamoDB, déploiement AWS, CI/CD Jenkins

## Fonctionnalités principales
- **API Python (FastAPI)** pour discuter avec l’IA Mistral
- **Persistance des conversations** dans DynamoDB (clé primaire PK=USER#{telegram_id}, clé de tri SK=MSG#{timestamp})
- **Endpoints REST** pour enregistrer et récupérer l’historique des conversations
- **Déploiement AWS** (SAM, Lambda, API Gateway)
- **CI/CD Jenkins**

## Structure du projet
```
├── src/
│   ├── main.py         # API FastAPI
│   ├── utils.py        # Fonctions utilitaires (DynamoDB, logs...)
│   └── config.py       # Configuration (env, clés...)
├── infrastructure/
│   └── template.yaml   # Template CloudFormation SAM
├── tests/              # Tests unitaires
├── Jenkinsfile         # Pipeline CI/CD Jenkins
├── Makefile            # Commandes utiles (build, test, deploy...)
├── requirements.txt    # Dépendances Python
└── .env                # Variables d’environnement (non versionné)
```


## Endpoints principaux
- `POST /conversation/start` : Démarre une nouvelle conversation et retourne un `conversation_id`
- `GET /conversation/active/{telegram_id}` : Récupère le dernier `conversation_id` actif pour un utilisateur
- `POST /conversation/message` : Enregistre un message utilisateur + réponse bot dans une conversation
- `POST /conversation/{conversation_id}/close` : Clôture une conversation (status=closed)
- `GET /conversation/{conversation_id}/history?telegram_id=...` : Récupère l’historique d’une conversation précise
- `GET /conversation/history/{telegram_id}` : Récupère l’historique de tous les messages d’un utilisateur
- `GET /chat?question=...` : Envoie une question à l’IA Mistral
- `GET /` : Redirige vers la documentation Swagger

## Exemple d’utilisation


### Démarrer une conversation
```bash
curl -X POST http://localhost:8000/conversation/start \
  -H 'Content-Type: application/json' \
  -d '{"telegram_id": "123456"}'
# Réponse : { "conversation_id": "..." }
```

### Récupérer la dernière conversation active
```bash
curl http://localhost:8000/conversation/active/123456
# Réponse : { "conversation_id": "..." }
```

### Enregistrer un message dans une conversation
```bash
curl -X POST http://localhost:8000/conversation/message \
  -H 'Content-Type: application/json' \
  -d '{
    "telegram_id": "123456",
    "conversation_id": "abc-uuid",
    "user_message": "Bonjour !",
    "bot_response": "Salut, comment puis-je t'aider ?"
  }'
```

### Clôturer une conversation
```bash
curl -X POST http://localhost:8000/conversation/abc-uuid/close \
  -H 'Content-Type: application/json' \
  -d '{"telegram_id": "123456"}'
```

### Récupérer l’historique d’une conversation
```bash
curl "http://localhost:8000/conversation/abc-uuid/history?telegram_id=123456"
```

### Récupérer l’historique de tous les messages d’un utilisateur
```bash
curl http://localhost:8000/conversation/history/123456
```

### Discuter avec l’IA
```bash
curl "http://localhost:8000/chat?question=Bonjour%20IA"
```

## Déploiement local

1. Installer les dépendances :
   ```bash
   make venv
   make install
   ```
2. Lancer l’API :
   ```bash
   uvicorn src.main:app --reload
   ```
3. Accéder à la doc interactive : [http://localhost:8000](http://localhost:8000)

## Déploiement AWS
- Utiliser le Makefile (`make build`, `make deploy`) et le template SAM (`infrastructure/template.yaml`)
- Variables d’environnement à renseigner dans `.env`

## CI/CD Jenkins
- Pipeline défini dans `Jenkinsfile` : tests, build, déploiement, test endpoint

## Contraintes DynamoDB
- **Aucune opération Scan n’est autorisée** (Query uniquement)
- Structure des clés :
  - PK = USER#{telegram_id}
  - SK = MSG#{timestamp}


## Bot Telegram : Workflow recommandé

1. **Démarrer ou reprendre une conversation**
   - Appeler `GET /conversation/active/{telegram_id}`
   - Si aucune conversation active, appeler `POST /conversation/start` pour en créer une nouvelle
2. **Envoyer un message**
   - Appeler `GET /chat?question=...` pour obtenir la réponse IA
   - Appeler `POST /conversation/message` pour enregistrer la question/réponse dans la conversation
3. **Clôturer la conversation**
   - Appeler `POST /conversation/{conversation_id}/close` si l'utilisateur tape `/close` ou `/new`
4. **Afficher l’historique**
   - Appeler `GET /conversation/{conversation_id}/history?telegram_id=...`

**Le bot ne doit jamais stocker d’état en RAM.**
Chaque action doit interroger l’API pour obtenir le `conversation_id` courant ou en créer un nouveau.

---

© ESGIS 2025 – Projet Chatbot Python/Mistral/AWS
