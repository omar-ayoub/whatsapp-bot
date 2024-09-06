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
        client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    return client

def get_db_connection():
    conn = psycopg2.connect(current_app.config['DATABASE_URL'])
    return conn

def get_openai_response(sender, message):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT openai_thread_id FROM conversations WHERE sender = %s", (sender,))
            result = cur.fetchone()
            thread_id = result[0] if result else None

        client = get_openai_client()
        
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            with conn.cursor() as cur:
                cur.execute("INSERT INTO conversations (sender, openai_thread_id) VALUES (%s, %s) ON CONFLICT (sender) DO UPDATE SET openai_thread_id = EXCLUDED.openai_thread_id", (sender, thread_id))
            conn.commit()
        
        # Check for active runs
        active_runs = client.beta.threads.runs.list(thread_id=thread_id, status="in_progress")
        if active_runs.data:
            # Wait for the active run to complete (with a timeout)
            timeout = 30  # 30 seconds timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=active_runs.data[0].id)
                if run.status == "completed":
                    break
                time.sleep(1)
            else:
                return "I'm sorry, but the system is currently busy. Please try again in a moment."

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=current_app.config['OPENAI_ASSISTANT_ID']
        )

        # Wait for run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status == 'failed':
                return "I'm sorry, but I encountered an error. Please try again later."
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=thread_id)
        assistant_message = next((msg for msg in messages if msg.role == 'assistant'), None)
        
        if assistant_message and assistant_message.content:
            return assistant_message.content[0].text.value
        else:
            return "I'm sorry, but I couldn't generate a response. Please try again."
    except Exception as e:
        logger.error(f"Error in get_openai_response: {str(e)}")
        return "An error occurred while processing your request. Please try again later."
    finally:
        conn.close()