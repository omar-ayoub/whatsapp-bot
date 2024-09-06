
import requests

url = "https://api.openai.com/v1/assistants"
headers = {
    "Authorization": f"Bearer {'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'}",  # Replace with your actual API key
    "OpenAI-Organization": 'org-0QrDTrEbGvfae4VnfSmYfFsR',  # Replace with your organization ID if applicable
    "OpenAI-Beta": "assistants=v2"  # Required header for accessing the Assistants API
}

response = requests.get(url, headers=headers)

# Check if the response is successful
if response.status_code == 200:
    assistants = response.json().get('data', [])
    if assistants:
        print("List of Assistants:")
        for assistant in assistants:
            print(f"ID: {assistant['id']}, Name: {assistant.get('name', 'Unnamed')}")
    else:
        print("No assistants found.")
else:
    print(f"Failed to retrieve assistants: {response.status_code} - {response.json()}")
