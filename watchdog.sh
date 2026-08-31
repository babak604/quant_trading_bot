#!/bin/bash
URL="http://localhost:8501/"

if ! curl -s --head --request GET "$URL" | grep "200 OK" > /dev/null; then
    echo "$(date): Streamlit portal down on port 8501. Restarting systemd service..." >> /home/ubuntu/quant_trading_bot/watchdog.log
    sudo systemctl restart streamlit-dashboard
fi
