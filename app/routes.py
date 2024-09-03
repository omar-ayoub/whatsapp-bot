from flask import Blueprint, request, jsonify, current_app
from .services.whatsapp_service import process_whatsapp_message
from .models import Conversation
from . import db

main = Blueprint('main', __name__)

@main.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == current_app.config['VERIFY_TOKEN']:
            return challenge, 200
        else:
            return 'Forbidden', 403
    return 'Bad Request', 400

@main.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data['object'] == 'whatsapp_business_account':
        for entry in data['entry']:
            for change in entry['changes']:
                if change['field'] == 'messages':
                    for message in change['value'].get('messages', []):
                        if message['type'] == 'text':
                            sender = message['from']
                            text = message['text']['body']
                            
                            conversation = Conversation.query.filter_by(sender=sender).first()
                            if not conversation:
                                conversation = Conversation(sender=sender)
                                db.session.add(conversation)
                            
                            conversation.messages.append(text)
                            db.session.commit()
                            
                            process_whatsapp_message(sender, text)
    return jsonify({"status": "success"}), 200