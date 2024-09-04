from openai import OpenAI
from flask import current_app
from ..models import Conversation
from .. import db
import logging

client = None

def get_openai_client():
    global client
    if client is None:
        client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    return client

def get_openai_response(sender, message):
    logger = logging.getLogger(__name__)
    conversation = Conversation.query.filter_by(sender=sender).first()
    client = get_openai_client()
    
    if not conversation.openai_thread_id:
        thread = client.beta.threads.create()
        conversation.openai_thread_id = thread.id
        db.session.commit()
        logger.debug(f"New thread created with ID: {thread.id} for sender: {sender}")

    try:
        client.beta.threads.messages.create(
            thread_id=conversation.openai_thread_id,
            role="user",
            content=message
        )
        logger.debug(f"Message sent to OpenAI: {message}")
    except Exception as e:
        logger.error(f"Failed to create message in thread: {str(e)}")
        return "Error sending message to Assistant API."

    try:
        run = client.beta.threads.runs.create(
            thread_id=conversation.openai_thread_id,
            assistant_id=current_app.config['OPENAI_ASSISTANT_ID']
        )
        logger.debug(f"Run created with ID: {run.id} for thread: {conversation.openai_thread_id}")
    except Exception as e:
        logger.error(f"Error creating run in OpenAI: {str(e)}")
        return "Error creating Assistant API run."

    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=conversation.openai_thread_id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            logger.debug("Run completed successfully.")
            break
        elif run_status.status == 'failed':
            logger.error("Assistant API run failed.")
            return "I'm sorry, but I encountered an error. Please try again later."

    try:
        messages = client.beta.threads.messages.list(thread_id=conversation.openai_thread_id)
        assistant_message = next((msg for msg in messages if msg.role == 'assistant'), None)
        if assistant_message and assistant_message.content:
            response_text = assistant_message.content[0].text.value
            logger.debug(f"Assistant response: {response_text}")
            return response_text
        else:
            logger.error("No response content found from Assistant.")
            return "I'm sorry, but I couldn't generate a response. Please try again."
    except Exception as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        return "Error retrieving response from Assistant."