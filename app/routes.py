from flask import Blueprint, request, jsonify
from .models import Conversation
from . import db
import logging

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main.route('/')
def index():
    return "WhatsApp Bot API is running!"

@main.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    logger.debug(f"Webhook verification: mode={mode}, token={token}, challenge={challenge}")

    if mode and token:
        if mode == 'subscribe' and token == 'YOUR_VERIFY_TOKEN':
            logger.info("Webhook verified")
            return challenge, 200
        else:
            logger.warning("Webhook verification failed")
            return 'Forbidden', 403
    return 'Bad Request', 400

@main.route('/webhook', methods=['POST'])
def webhook():
    logger.debug(f"Received webhook: {request.json}")
    data = request.json
    if data['object'] == 'whatsapp_business_account':
        for entry in data['entry']:
            for change in entry['changes']:
                if change['field'] == 'messages':
                    for message in change['value'].get('messages', []):
                        if message['type'] == 'text':
                            sender = message['from']
                            text = message['text']['body']
                            
                            logger.info(f"Received message from {sender}: {text}")
                            
                            try:
                                conversation = Conversation.query.filter_by(sender=sender).first()
                                if not conversation:
                                    conversation = Conversation(sender=sender)
                                    db.session.add(conversation)
                                
                                conversation.messages = str(conversation.messages) + f"\n{text}"  # Append new message
                                db.session.commit()
                                logger.info(f"Conversation updated for {sender}")
                            except Exception as e:
                                logger.error(f"Error updating conversation: {str(e)}")
                                return jsonify({"status": "error", "message": str(e)}), 500
                            
                            # Here you would process the message and send a response
                            # For now, let's just log it
                            logger.info(f"Processing message: {text}")
    
    return jsonify({"status": "success"}), 200