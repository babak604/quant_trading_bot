import os, sys, requests
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/quant_trading_bot/.env')

WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")

def send_alert():
    if not WEBHOOK_URL:
        print("No ALERT_WEBHOOK_URL set. Skipping notification.")
        sys.exit(0)

    service_name = sys.argv[1] if len(sys.argv) > 1 else "quant-keeper"
    
    discord_payload = {
        "embeds": [
            {
                "title": f"🚨 Service Failure Alert: {service_name}",
                "description": f"The `{service_name}` daemon on Arbitrum Sepolia has crashed or exited unexpectedly.",
                "color": 15158332,
                "fields": [
                    {"name": "Host", "value": "The1 (Ubuntu VPS)", "inline": True},
                    {"name": "Action Required", "value": "Check logs: `journalctl -u quant-keeper -n 50`", "inline": False}
                ]
            }
        ]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=discord_payload, timeout=10)
        if response.status_code in [200, 204]:
            print("Alert notification sent successfully to Discord.")
        else:
            print(f"Failed to send alert: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending webhook alert: {e}")

if __name__ == "__main__":
    send_alert()
