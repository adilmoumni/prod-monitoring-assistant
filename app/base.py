import requests
import json 
import os 

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def send_slack_alert(error_logs, severity="ERROR", dry_run=False):
    """Sends an error message with GCP logs."""

    payload = {
        "attachments": [
            {
                "fallback": f"*{severity} in production",
                "text": f"```{error_logs}```",

            }
        ]
    }

    if dry_run:
        print("[Test] Slack alert:", json.dumps(payload, indent=2))
        return

    headers = {"Content-Type": "application/json"}
    response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload), headers=headers)

    if response.status_code != 200:
        print(f"Error while sending message to Slack: {response.text}")
