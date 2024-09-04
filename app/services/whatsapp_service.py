import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def log_http_response(response):
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Content-type: {response.headers.get('content-type')}")
    logger.info(f"Body: {response.text}")

def send_whatsapp_message(recipient, message):
    url = f"https://graph.facebook.com/v13.0/{current_app.config['WHATSAPP_PHONE_NUMBER_ID']}/messages"
    headers = {
        'Authorization': f"Bearer {current_app.config['WHATSAPP_TOKEN']}",
        'Content-Type': 'application/json'
    }
    data = {
        'messaging_product': 'whatsapp',
        'to': recipient,
        'type': 'text',
        'text': {'body': message}
    }
    logger.debug(f"Sending message to {recipient}: {message}")
    logger.debug(f"URL: {url}")
    logger.debug(f"Headers: {headers}")
    logger.debug(f"Data: {data}")
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        log_http_response(response)
        return response.json()
    except requests.Timeout:
        logger.error("Timeout occurred while sending message")
        return {"status": "error", "message": "Request timed out"}
    except requests.RequestException as e:
        logger.error(f"Request failed due to: {e}")
        return {"status": "error", "message": str(e)}