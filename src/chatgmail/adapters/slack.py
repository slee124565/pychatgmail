import requests
import json


def send_slack_message(ch_webhook: str, msg: str):
    # ch_webhook = "https://hooks.slack.com/services/T81A/BMHDC2AZ/FXdcEc2LqV1sApKUojZoFbKR"
    headers = {
        "Content-type": "application/json"
    }
    data = {
        "text": msg
    }
    response = requests.post(ch_webhook, headers=headers, data=json.dumps(data))
    response.raise_for_status()
