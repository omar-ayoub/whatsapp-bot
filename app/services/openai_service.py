import time
from openai import OpenAI
from flask import current_app
import psycopg2
import logging

logger = logging.getLogger(__name__)

client = None

def get_openai_client():
    global client
    if client is None:
        client = OpenAI(
            api_key=current_app.config['OPENAI_API_KEY'],
            organization=current_app.config.get('OPENAI_ORGANIZATION_ID')
        )
    return client

def create_openai_thread():
    client = get_openai_client()
    try:
        response = client.beta.threads.create(
            headers={
                "OpenAI-Organization": current_app.config['OPENAI_ORGANIZATION_ID'],
                "OpenAI-Beta": "assistants=v2"
            }
        )
        thread_id = response['id']
        logger.info(f"Successfully created OpenAI thread with ID: {thread_id}")
        return thread_id
    except Exception as e:
        logger.error(f"Error creating OpenAI thread: {str(e)}")
        return None

def process_with_openai(thread_id, message):
    client = get_openai_client()
    try:
        # Send message to OpenAI with the correct headers
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message,
            headers={
                "OpenAI-Organization": current_app.config['OPENAI_ORGANIZATION_ID'],
                "OpenAI-Beta": "assistants=v2"
            }
        )
        logger.info(f"Message sent to OpenAI thread {thread_id}")

        # Create a run to process the message with the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=current_app.config['OPENAI_ASSISTANT_ID'],
            headers={
                "OpenAI-Organization": current_app.config['OPENAI_ORGANIZATION_ID'],
                "OpenAI-Beta": "assistants=v2"
            }
        )
        logger.info(f"Run created: {run.id}")

        # Wait for run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
                headers={
                    "OpenAI-Organization": current_app.config['OPENAI_ORGANIZATION_ID'],
                    "OpenAI-Beta": "assistants=v2"
                }
            )
            logger.info(f"Run status: {run_status.status}")
            if run_status.status == 'completed':
                break
            elif run_status.status == 'failed':
                logger.error(f"Run failed: {run_status.last_error}")
                return "I'm sorry, but I encountered an error. Please try again later."
            time.sleep(1)

        # Retrieve messages to find the assistant's response
        messages = client.beta.threads.messages.list(
            thread_id=thread_id,
            headers={
                "OpenAI-Organization": current_app.config['OPENAI_ORGANIZATION_ID'],
                "OpenAI-Beta": "assistants=v2"
            }
        )
        logger.info(f"Retrieved {len(messages.data)} messages from thread {thread_id}")

        assistant_message = next((msg for msg in messages.data if msg.role == 'assistant'), None)
        if assistant_message and assistant_message.content:
            response = assistant_message.content[0].text.value
            logger.info(f"Assistant response: {response}")
            return response

        logger.warning("No assistant response found.")
        return "I'm sorry, I couldn't generate a response. Please try again."
    except Exception as e:
        logger.error(f"Error in process_with_openai: {str(e)}")
        return "An error occurred while processing your request."

def get_openai_response(sender, message):
    """
    Main function to handle getting a response from the OpenAI assistant.

    Args:
        sender (str): The sender's identifier, used to track conversation threads.
        message (str): The message content sent by the user.

    Returns:
        str: The assistant's response or an error message.
    """
    # Create or retrieve the thread ID for the sender
    thread_id = create_openai_thread()
    
    if not thread_id:
        logger.error("Unable to create or retrieve thread for user.")
        return "I'm having trouble starting the conversation. Please try again later."

    # Process the message using the OpenAI assistant
    response = process_with_openai(thread_id, message)
    return response
