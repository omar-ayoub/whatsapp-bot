from flask import Blueprint, request, jsonify, current_app
import logging
from .services.whatsapp_service import send_whatsapp_message
from .services.openai_service import get_openai_response
import time
import os

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main.route('/')
def index():
    logger.info("Root route accessed")
    return jsonify({
        "status": "success",
        "message": "WhatsApp Bot API is running!",
        "environment": os.environ.get('FLASK_ENV', 'production'),
        "debug": current_app.debug
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

    logger.info(f"Webhook verification attempt: mode={mode}, token={token}, challenge={challenge}")
    logger.info(f"Expected token: {current_app.config['VERIFY_TOKEN']}")

    if mode and token:
        if mode == 'subscribe' and token == current_app.config['VERIFY_TOKEN']:
            logger.info("Webhook verified successfully")
            return challenge, 200
        else:
            logger.warning(f"Webhook verification failed. Received token: {token}, Expected token: {current_app.config['VERIFY_TOKEN']}")
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
    # Implement your conversation update logic here
    pass

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

message_timestamps = {}