from openai import OpenAI
from flask import current_app
from ..models import Conversation
from .. import db

client = None

def get_openai_client():
    global client
    if client is None:
        client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    return client

def get_openai_response(sender, message):
    conversation = Conversation.query.filter_by(sender=sender).first()
    client = get_openai_client()
    
    if not conversation.openai_thread_id:
        thread = client.beta.threads.create()
        conversation.openai_thread_id = thread.id
        db.session.commit()
    
    client.beta.threads.messages.create(
        thread_id=conversation.openai_thread_id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=conversation.openai_thread_id,
        assistant_id=current_app.config['OPENAI_ASSISTANT_ID']
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=conversation.openai_thread_id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
        elif run_status.status == 'failed':
            return "I'm sorry, but I encountered an error. Please try again later."

    messages = client.beta.threads.messages.list(thread_id=conversation.openai_thread_id)
    assistant_message = next((msg for msg in messages if msg.role == 'assistant'), None)
    
    if assistant_message and assistant_message.content:
        return assistant_message.content[0].text.value
    else:
        return "I'm sorry, but I couldn't generate a response. Please try again."