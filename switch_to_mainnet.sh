#!/bin/bash
set -e

echo "=== mor.money Mainnet Switchboard ==="

# 1. Verify Balance
python3 /home/ubuntu/quant_trading_bot/deploy_mainnet.py

# 2. Deploy Contracts if needed
echo "Deploying Stylus Engine to Mainnet..."
cd /home/ubuntu/quant_trading_bot/stylus_engine
MAINNET_KEY=$(grep DEPLOYER_PRIVATE_KEY /home/ubuntu/quant_trading_bot/.env.mainnet | cut -d '=' -f2 | tr -d '"'\'' ')

cargo stylus deploy \
  --endpoint https://arb1.arbitrum.io/rpc \
  --private-key $MAINNET_KEY

# 3. Stop Sepolia Service and Enable Mainnet Service
echo "Switching Systemd Services..."
sudo systemctl stop quant-keeper
sudo systemctl enable --now quant-keeper-mainnet

echo "mor.money is now live on Arbitrum One Mainnet!"
journalctl -u quant-keeper-mainnet -f -n 20
