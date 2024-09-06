from flask import Blueprint, request, jsonify, current_app
import logging
from .services.whatsapp_service import send_whatsapp_message
from .services.openai_service import get_openai_response
import time
import os
from . import db
from .models import User, Thread, Message
import openai

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)
message_timestamps = {}

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
        return process_webhook()

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

def process_webhook():
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
                                # Find or create user
                                user = User.query.filter_by(phone_number=sender).first()
                                if not user:
                                    user = User(phone_number=sender)
                                    db.session.add(user)
                                    db.session.commit()
                                    logger.info(f"Created new user: {sender}")

                                # Find or create thread
                                thread = Thread.query.filter_by(user_id=user.id).order_by(Thread.created_at.desc()).first()
                                if not thread:
                                    openai_thread_id = create_openai_thread()
                                    if not openai_thread_id:
                                        logger.error("Failed to create OpenAI thread, unable to proceed.")
                                        send_whatsapp_message(sender, "Error: Unable to create a conversation thread. Please try again later.")
                                        return jsonify({"status": "error", "message": "Thread creation failed"}), 500

                                    thread = Thread(user_id=user.id, openai_thread_id=openai_thread_id)
                                    db.session.add(thread)
                                    db.session.commit()
                                    logger.info(f"Created new thread with ID: {thread.openai_thread_id} for user {user.phone_number}")

                                # Add message to thread
                                if not thread.id:
                                    logger.error(f"Invalid thread ID for user {user.id}")
                                    send_whatsapp_message(sender, "Error: Unable to process your message at the moment.")
                                    return jsonify({"status": "error", "message": "Invalid thread ID"}), 500

                                new_message = Message(thread_id=thread.id, content=text, is_from_user=True, sender_phone=sender)
                                db.session.add(new_message)
                                db.session.commit()
                                logger.info(f"Message added to thread {thread.openai_thread_id}")

                                # Process message with OpenAI
                                response = process_with_openai(thread.openai_thread_id, text)

                                # Send response back to user
                                send_whatsapp_message(sender, response)

                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")
                                send_whatsapp_message(sender, "I'm sorry, but I encountered an error. Please try again later.")

    return jsonify({"status": "success"}), 200

def should_ignore_message(sender):
    current_time = time.time()
    return sender in message_timestamps and current_time - message_timestamps[sender] < 5

def update_message_timestamp(sender):
    message_timestamps[sender] = time.time()

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

def create_openai_thread():
    client = openai.Client(api_key=current_app.config['OPENAI_API_KEY'])
    thread = client.beta.threads.create()
    return thread.id

def process_with_openai(thread_id, message):
    client = openai.Client(api_key=current_app.config['OPENAI_API_KEY'])
    
    logger.info(f"Sending message to OpenAI: thread_id={thread_id}, message={message}")
    
    try:
        # Send message to OpenAI
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        logger.info("Message sent to OpenAI successfully")
        
        # Create and wait for run to complete
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=current_app.config['OPENAI_ASSISTANT_ID']
        )
        logger.info(f"Run created: {run.id}")
        
        while run.status != 'completed':
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            logger.info(f"Run status: {run.status}")
            if run.status == 'failed':
                logger.error(f"Run failed: {run.last_error}")
                return "I encountered an error while processing your request."
            time.sleep(1)
        
        # Retrieve messages
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        logger.info(f"Retrieved {len(messages.data)} messages")
        
        # Find the latest assistant message
        for msg in messages.data:
            if msg.role == 'assistant':
                response = msg.content[0].text.value
                logger.info(f"Assistant response: {response}")
                return response
        
        logger.warning("No assistant response found")
        return "I'm sorry, I couldn't generate a response."
    
    except Exception as e:
        logger.error(f"Error in process_with_openai: {str(e)}")
        return "An error occurred while processing your request."