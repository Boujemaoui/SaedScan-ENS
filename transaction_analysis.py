"""
transaction_analysis.py - Ethereum Transaction Forensic Tool
"""

from web3 import Web3
import requests
from typing import Dict, List
import json

class TransactionAnalyzer:
    def __init__(self, w3: Web3):
        self.w3 = w3
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        
    def get_transaction_flow(self, tx_hash: str) -> Dict:
        """Map input/output flow for a transaction"""
        tx = self.w3.eth.get_transaction(tx_hash)
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        
        return {
            'from': tx['from'],
            'to': tx['to'],
            'value': self.w3.fromWei(tx['value'], 'ether'),
            'contract_interaction': receipt['contractAddress'] is not None,
            'gas_used': receipt['gasUsed']
        }

    def detect_anomalies(self, tx_data: Dict) -> List[str]:
        """Flag potential red flags"""
        alerts = []
        if tx_data['value'] > 100:  # Whale alert threshold (ETH)
            alerts.append("High-value transaction (>100 ETH)")
        if not tx_data['to']:  # Contract creation
            alerts.append("Contract deployment")
        return alerts

    def fetch_token_transfers(self, tx_hash: str) -> List[Dict]:
        """Get ERC20/721 transfers in transaction"""
        url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionReceipt&txhash={tx_hash}&apikey={self.etherscan_api_key}"
        response = requests.get(url)
        return response.json().get('result', {}).get('logs', [])

# Example usage
if __name__ == "__main__":
    w3 = Web3(Web3.HTTPProvider(os.getenv('INFURA_URL')))
    analyzer = TransactionAnalyzer(w3)
    
    sample_tx = "0x..."  # Replace with actual TX hash
    flow = analyzer.get_transaction_flow(sample_tx)
    print(f"Transaction Analysis:\n{json.dumps(flow, indent=2)}")
    print(f"Alerts: {analyzer.detect_anomalies(flow)}")
