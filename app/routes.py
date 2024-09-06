from flask import Blueprint, request, jsonify, current_app
import logging
import psycopg2
from psycopg2 import sql
from .services.whatsapp_service import send_whatsapp_message
from .services.openai_service import get_openai_response
import time

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

message_timestamps = {}

def get_db_connection():
    conn = psycopg2.connect(current_app.config['DATABASE_URL'])
    return conn

@main.route('/')
def index():
    logger.info("Root route accessed")
    return jsonify({
        "status": "success",
        "message": "WhatsApp Bot API is running!",
        "environment": current_app.config['FLASK_ENV'],
        "debug": current_app.config['DEBUG']
    }), 200

@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        return process_webhook(request)

def verify_webhook(request):
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == current_app.config['VERIFY_TOKEN']:
            logger.info("Webhook verified successfully")
            return challenge, 200
        else:
            logger.warning("Webhook verification failed")
            return 'Forbidden', 403
    return 'Bad Request', 400

def process_webhook(request):
    logger.debug(f"Received webhook: {request.json}")
    data = request.json
    if is_valid_whatsapp_message(data):
        for entry in data['entry']:
            for change in entry['changes']:
                if change['field'] == 'messages':
                    for message in change['value'].get('messages', []):
                        if message['type'] == 'text':
                            sender = message['from']
                            text = message['text']['body']
                            
                            if should_ignore_message(sender):
                                logger.info(f"Ignoring duplicate message from {sender}")
                                return jsonify({"status": "success"}), 200
                            
                            update_message_timestamp(sender)
                            
                            logger.info(f"Received message from {sender}: {text}")
                            
                            try:
                                update_conversation(sender, text)
                                response = get_openai_response(sender, text)
                                logger.debug(f"Processed response: {response}")
                                result = send_whatsapp_message(sender, response)
                                logger.debug(f"WhatsApp send result: {result}")
                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")
                                return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "success"}), 200

def should_ignore_message(sender):
    current_time = time.time()
    return sender in message_timestamps and current_time - message_timestamps[sender] < 5

def update_message_timestamp(sender):
    message_timestamps[sender] = time.time()

def update_conversation(sender, text):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversations (sender, messages)
                VALUES (%s, %s)
                ON CONFLICT (sender) DO UPDATE
                SET messages = conversations.messages || E'\n' || %s
            """, (sender, text, text))
        conn.commit()
        logger.info(f"Conversation updated for {sender}")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Database error updating conversation: {str(e)}")
        raise
    finally:
        conn.close()

def is_valid_whatsapp_message(body):
    valid = (
        body.get("object") == "whatsapp_business_account"
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
    logger.debug(f"Is valid WhatsApp message: {valid}")
    return valid