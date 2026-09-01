import os, time, requests
from web3 import Web3

RPC_URL = os.getenv('ARBITRUM_SEPOLIA_RPC', 'https://sepolia-rollup.arbitrum.io/rpc')
STYLUS_CONTRACT = os.getenv('STYLUS_CONTRACT_ADDRESS', '0x2f615143c5ea1db83834ea4508528f199ab9c462')
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def listen_events():
    print(f'[Stylus Event Listener] Connected: {w3.is_connected()}')
    last_block = w3.eth.block_number
    while True:
        try:
            curr = w3.eth.block_number
            if curr > last_block:
                print(f'[Stylus Listener] Block {last_block + 1} -> {curr}')
                last_block = curr
        except Exception as e:
            print(f'Error: {e}')
        time.sleep(12)

if __name__ == '__main__':
    listen_events()
