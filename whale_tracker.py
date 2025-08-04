"""
whale_tracker.py - Ethereum Whale Activity Monitor
"""

from web3 import Web3
import os
from typing import Dict, List
import time

class WhaleTracker:
    def __init__(self, w3: Web3):
        self.w3 = w3
        self.whale_threshold = 100  # ETH
        self.exchange_addresses = {
            'Binance': '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE',
            'Coinbase': '0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43'
        }

    def detect_whale_transfers(self, block_range: int = 100) -> List[Dict]:
        """Scan recent blocks for large transfers"""
        latest_block = self.w3.eth.block_number
        whale_txs = []
        
        for block_num in range(latest_block - block_range, latest_block):
            block = self.w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                value_eth = self.w3.fromWei(tx.value, 'ether')
                if value_eth >= self.whale_threshold:
                    whale_txs.append({
                        'hash': tx.hash.hex(),
                        'from': tx['from'],
                        'to': tx['to'],
                        'value': float(value_eth),
                        'block': block_num
                    })
        return whale_txs

    def is_exchange_flow(self, tx: Dict) -> bool:
        """Check if transaction involves known exchange addresses"""
        return (tx['from'] in self.exchange_addresses.values() or 
                tx['to'] in self.exchange_addresses.values())

if __name__ == "__main__":
    w3 = Web3(Web3.HTTPProvider(os.getenv('INFURA_URL')))
    tracker = WhaleTracker(w3)
    
    print("🕵️ Tracking whale transactions...")
    whales = tracker.detect_whale_transfers(block_range=50)
    
    for tx in whales:
        alert = f"🚨 WHALE ALERT: {tx['value']} ETH from {tx['from'][:6]}..."
        if tracker.is_exchange_flow(tx):
            alert += " (Exchange-related)"
        print(alert)
