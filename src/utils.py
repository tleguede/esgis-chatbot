from datetime import datetime
import json
from uuid import uuid4
import logging
from typing import List

import boto3

from src.config import env_vars
## Simple edit


class Utils:
    @staticmethod
    def set_conversation_metadata(conversation_id: str, telegram_id: str, status: str = "active"):
        """
        Create or update the metadata item for a conversation (PK=CONV#<conversation_id>, SK=METADATA).
        """
        dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        item = {
            'PK': {'S': f'CONV#{conversation_id}'},
            'SK': {'S': 'METADATA'},
            'conversation_id': {'S': conversation_id},
            'telegram_id': {'S': telegram_id},
            'status': {'S': status},
        }
        dynamo_client.put_item(
            TableName=env_vars.DYNAMO_TABLE,
            Item=item,
        )

    @staticmethod
    def get_conversation_metadata(conversation_id: str):
        """
        Get the metadata item for a conversation (PK=CONV#<conversation_id>, SK=METADATA).
        """
        dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        response = dynamo_client.get_item(
            TableName=env_vars.DYNAMO_TABLE,
            Key={
                'PK': {'S': f'CONV#{conversation_id}'},
                'SK': {'S': 'METADATA'}
            }
        )
        return response.get('Item')
    @staticmethod
    def close_conversation(conversation_id: str, telegram_id: str):
        """
        Mark a conversation as closed by updating its metadata item (PK=CONV#<conversation_id>, SK=METADATA).
        """
        Utils.set_conversation_metadata(conversation_id, telegram_id, status="closed")

    @staticmethod
    def get_last_active_conversation(telegram_id: str):
        """
        Retourne le dernier conversation_id actif (status != closed) pour un utilisateur.
        Utilise le GSI sur telegram_id pour les items de métadonnées (PK=CONV#<conversation_id>, SK=METADATA) si disponible.
        Fallback sur Scan si le GSI n'est pas encore déployé.
        """
        dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        try:
            # Essayons d'utiliser le GSI (GSI-TelegramId-Metadata)
            response = dynamo_client.query(
                TableName=env_vars.DYNAMO_TABLE,
                IndexName="GSI-TelegramId-Metadata",
                KeyConditionExpression="telegram_id = :tid AND SK = :meta",
                ExpressionAttributeValues={
                    ':tid': {'S': telegram_id},
                    ':meta': {'S': 'METADATA'}
                },
                ScanIndexForward=False,  # du plus récent au plus ancien
                Limit=50
            )
            items = response.get('Items', [])
        except Exception as e:
            # Si le GSI n'existe pas encore, fallback sur Scan (dev/test only)
            items = []
            try:
                response = dynamo_client.scan(
                    TableName=env_vars.DYNAMO_TABLE,
                    FilterExpression="telegram_id = :tid AND SK = :meta",
                    ExpressionAttributeValues={
                        ':tid': {'S': telegram_id},
                        ':meta': {'S': 'METADATA'}
                    },
                    Limit=50
                )
                items = response.get('Items', [])
            except Exception as e2:
                Utils.log_error(f"Erreur lors de la recherche de conversation active: {e2}")
                return None
        # Find the most recent active conversation (not closed)
        for item in sorted(items, key=lambda x: x.get('PK', {}).get('S', ''), reverse=True):
            if item.get('status', {}).get('S', 'active') != 'closed':
                return item.get('conversation_id', {}).get('S', None)
        return None

    @staticmethod
    def start_conversation(telegram_id: str) -> str:
        """
        Crée un nouvel identifiant de conversation (UUID), crée le metadata item (status=active), et retourne cet ID.
        """
        conversation_id = str(uuid4())
        Utils.set_conversation_metadata(conversation_id, telegram_id, status="active")
        return conversation_id

    @staticmethod
    def get_conversation_history_by_id(conversation_id: str, telegram_id: str = None, limit: int = 50):
        """
        Récupère l'historique des messages pour un conversation_id donné (optionnellement filtré par telegram_id).
        Nécessite que conversation_id soit un attribut dans chaque item.
        """
        dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        # Utilisation de Query avec FilterExpression (pas optimal, mais pas de Scan)
        # Si un GSI sur conversation_id existe, il faudrait l'utiliser ici
        key_condition = 'PK = :pk'
        expr_attr = {':pk': {'S': f'USER#{telegram_id}'}}
        response = dynamo_client.query(
            TableName=env_vars.DYNAMO_TABLE,
            KeyConditionExpression=key_condition,
            FilterExpression='conversation_id = :cid',
            ExpressionAttributeValues={**expr_attr, ':cid': {'S': conversation_id}},
            Limit=limit,
            ScanIndexForward=True
        )
        return response.get('Items', [])
    @staticmethod
    def save_conversation_message(telegram_id: str, conversation_id: str, user_message: str, bot_response: str, timestamp: str = None):
        """
        Enregistre un message de conversation dans DynamoDB avec la structure PK/SK recommandée.
        """
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()
        item = {
            'PK': {'S': f'USER#{telegram_id}'},
            'SK': {'S': f'MSG#{timestamp}'},
            'conversation_id': {'S': conversation_id},
            'user_message': {'S': user_message},
            'bot_response': {'S': bot_response},
            'timestamp': {'S': timestamp},
        }
        dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        dynamo_client.put_item(
            TableName=env_vars.DYNAMO_TABLE,
            Item=item,
        )

    @staticmethod
    def get_conversation_history(telegram_id: str, limit: int = 20):
        """
        Récupère l'historique des messages d'un utilisateur via Query (jamais Scan).
        """
        dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        response = dynamo_client.query(
            TableName=env_vars.DYNAMO_TABLE,
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': {'S': f'USER#{telegram_id}'},
            },
            Limit=limit,
            ScanIndexForward=True  # Chronological order
        )
        return response.get('Items', [])

    ALLOWED_EXTENSIONS = ["pdf", "docx", "doc", "png", "jpg", "jpeg"]

    @staticmethod
    def log_info(message):
        """_summary_
        Log a simple info message
        """
        logging.getLogger("uvicorn.error").info(msg=f"==> {message}")

    @staticmethod
    def log_debug(message):
        """_summary_
        Log a debug message
        """
        logging.getLogger("uvicorn.error").debug(msg=f"==> {message}")

    @staticmethod
    def log_error(message):
        """_summary_
        Log an error message
        """
        logging.getLogger("uvicorn.error").error(msg=f"==> {message}")

    @staticmethod
    def log_list(elements: List[any]):
        if elements:
            logging.getLogger("uvicorn.error").info(
                msg=f"Displaying all the {len(elements)} elements of the list"
            )
            for i in range(len(elements)):
                logging.getLogger("uvicorn.error").info(
                    msg=f"##### {i} ==> {json.dumps(elements[i], indent=4)}"
                )

    @staticmethod
    def get_logger():
        return logging.getLogger("uvicorn.error")

    @staticmethod
    def get_session():
        return boto3.Session(
            region_name=env_vars.AWS_REGION_NAME, profile_name=env_vars.AWS_PROFILE
        )

    @staticmethod
    def insert_data(item):
        dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        dynamo_client.put_item(
            TableName=env_vars.DYNAMO_TABLE,
            Item=item,
        )
