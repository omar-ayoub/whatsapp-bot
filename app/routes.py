from flask import Blueprint, request, jsonify, current_app
from .models import Conversation
from . import db
import logging
from sqlalchemy import inspect
from .services.whatsapp_service import send_whatsapp_message
from .services.openai_service import get_openai_response

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main.route('/')
def index():
    return "WhatsApp Bot API is running!"

@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        logger.info(f"Webhook verification: mode={mode}, token={token}, challenge={challenge}")

        if mode and token:
            if mode == 'subscribe' and token == current_app.config['VERIFY_TOKEN']:
                logger.info("Webhook verified successfully")
                return challenge, 200
            else:
                logger.warning("Webhook verification failed")
                return 'Forbidden', 403
        return 'Bad Request', 400

    elif request.method == 'POST':
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
                                
                                logger.info(f"Received message from {sender}: {text}")
                                
                                try:
                                    # Check if the table exists
                                    inspector = inspect(db.engine)
                                    if 'conversation' not in inspector.get_table_names():
                                        logger.error("Conversation table does not exist")
                                        db.create_all()
                                        logger.info("Attempted to create conversation table")
                                    
                                    conversation = Conversation.query.filter_by(sender=sender).first()
                                    if not conversation:
                                        conversation = Conversation(sender=sender, messages="")
                                        db.session.add(conversation)
                                    
                                    conversation.messages += f"\n{text}"  # Append new message
                                    db.session.commit()
                                    logger.info(f"Conversation updated for {sender}")
                                except Exception as e:
                                    logger.error(f"Error updating conversation: {str(e)}")
                                    return jsonify({"status": "error", "message": str(e)}), 500
                                
                                # Process the message and send the response
                                try:
                                    response = get_openai_response(sender, text)
                                    logger.debug(f"Processed response: {response}")
                                    result = send_whatsapp_message(sender, response)
                                    logger.debug(f"WhatsApp send result: {result}")
                                except Exception as e:
                                    logger.error(f"Error processing message: {str(e)}")
                                    return jsonify({"status": "error", "message": str(e)}), 500
        return jsonify({"status": "success"}), 200

def is_valid_whatsapp_message(body):
    valid = (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
    logger.debug(f"Is valid WhatsApp message: {valid}")
    return valid