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
