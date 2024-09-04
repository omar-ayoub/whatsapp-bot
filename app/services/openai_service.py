from openai import OpenAI
import shelve
from flask import current_app
from ..models import Conversation
from .. import db
import logging
import os

# Configure logging settings
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app_debug.log")
    ]
)

logger = logging.getLogger(__name__)
client = None

def get_openai_client():
    global client
    if client is None:
        api_key = os.getenv('OPENAI_API_KEY')  # Changed to use os.getenv for direct access
        if not api_key:
            logger.error("OPENAI_API_KEY is not set.")
            raise ValueError("OPENAI_API_KEY is not configured in the environment.")
        client = OpenAI(api_key=api_key)
    return client

def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)

def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id

def get_openai_response(sender, message):
    client = get_openai_client()
    thread_id = check_if_thread_exists(sender)

    if thread_id is None:
        logger.info(f"Creating new thread for sender {sender}")
        thread = client.beta.threads.create()
        store_thread(sender, thread.id)
        thread_id = thread.id
    else:
        logger.info(f"Retrieving existing thread for sender {sender}")
        thread = client.beta.threads.retrieve(thread_id)

    try:
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        logger.debug(f"Message sent to OpenAI: {message}")

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=os.getenv('OPENAI_ASSISTANT_ID')
        )
        logger.debug(f"Run created for thread: {thread_id}")

        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                logger.debug("Run completed successfully.")
                break
            elif run_status.status == 'failed':
                logger.error("Assistant API run failed.")
                return "I'm sorry, but I encountered an error. Please try again later."

        messages = client.beta.threads.messages.list(thread_id=thread_id)
        assistant_message = next((msg for msg in messages if msg.role == 'assistant'), None)
        if assistant_message and assistant_message.content:
            response_text = assistant_message.content[0].text.value
            logger.debug(f"Assistant response: {response_text}")
            return response_text
        else:
            logger.error("No response content found from Assistant.")
            return "I'm sorry, but I couldn't generate a response. Please try again."
    except Exception as e:
        logger.error(f"Error retrieving response from Assistant: {str(e)}")
        return "Error retrieving response from Assistant."
