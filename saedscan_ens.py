import os
import requests
from web3 import Web3
from datetime import datetime
import argparse
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

class EthereumOSINTTool:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}"))
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        self.opensea_api_key = os.getenv('OPENSEA_API_KEY')
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) EthereumOSINTTool/1.0",
            "Accept": "application/json"
        }

    def validate_address(self, address):
        """Valida si una dirección Ethereum es válida"""
        return Web3.isAddress(address)

    def resolve_ens(self, ens_name):
        """Resuelve un nombre ENS a dirección Ethereum"""
        try:
            address = self.w3.ens.address(ens_name)
            return address if address else None
        except Exception as e:
            print(f"[!] Error resolviendo ENS: {e}")
            return None

    def get_balance(self, address):
        """Obtiene el balance de ETH en una dirección"""
        try:
            balance = self.w3.eth.get_balance(address)
            return self.w3.fromWei(balance, 'ether')
        except Exception as e:
            print(f"[!] Error obteniendo balance: {e}")
            return None

    def get_transactions(self, address, limit=5):
        """Obtiene las últimas transacciones de una dirección"""
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey={self.etherscan_api_key}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()
            if data['status'] == '1':
                return data['result'][:limit]
            return []
        except Exception as e:
            print(f"[!] Error obteniendo transacciones: {e}")
            return []

    def get_nfts(self, address, limit=5):
        """Obtiene los NFTs de una dirección usando OpenSea"""
        url = "https://api.opensea.io/api/v1/assets"
        params = {
            'owner': address,
            'limit': limit,
            'order_direction': 'desc'
        }
        headers = {**self.headers, 'X-API-KEY': self.opensea_api_key}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            return response.json().get('assets', [])
        except Exception as e:
            print(f"[!] Error obteniendo NFTs: {e}")
            return []

    def get_token_balances(self, address):
        """Obtiene balances de tokens ERC-20"""
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&apikey={self.etherscan_api_key}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()
            if data['status'] == '1':
                return self._process_token_data(data['result'])
            return []
        except Exception as e:
            print(f"[!] Error obteniendo tokens: {e}")
            return []

    def _process_token_data(self, token_txs):
        """Procesa datos de tokens para mostrar balances"""
        tokens = {}
        for tx in token_txs:
            token_symbol = tx['tokenSymbol']
            value = float(tx['value']) / (10 ** int(tx['tokenDecimal']))
            
            if token_symbol in tokens:
                tokens[token_symbol] += value
            else:
                tokens[token_symbol] = value
        return tokens

    def generate_report(self, address):
        """Genera un reporte completo de la dirección"""
        if not self.validate_address(address):
            if address.endswith('.eth'):
                address = self.resolve_ens(address)
                if not address:
                    return {"error": "No se pudo resolver ENS"}
            else:
                return {"error": "Dirección inválida"}

        report = {
            "address": address,
            "balance_eth": float(self.get_balance(address)),
            "transactions": self.get_transactions(address),
            "nfts": self.get_nfts(address),
            "tokens": self.get_token_balances(address),
            "timestamp": datetime.now().isoformat()
        }
        return report

def main():
    parser = argparse.ArgumentParser(description="Herramienta OSINT para análisis de billeteras Ethereum")
    parser.add_argument("address", help="Dirección Ethereum o nombre ENS (ej: 0x... o vitalik.eth)")
    parser.add_argument("--output", help="Guardar reporte en JSON", action="store_true")
    args = parser.parse_args()

    tool = EthereumOSINTTool()
    report = tool.generate_report(args.address)

    if "error" in report:
        print(f"[X] Error: {report['error']}")
        return

    print(f"\n🔍 Reporte para {report['address']}")
    print(f"💰 Balance: {report['balance_eth']} ETH")
    
    print("\n🪙 Tokens:")
    for token, balance in report['tokens'].items():
        print(f" - {token}: {balance:,.2f}")

    print("\n🖼 NFTs (Top 5):")
    for nft in report['nfts']:
        print(f" - {nft.get('name', 'Unnamed')} ({nft.get('asset_contract', {}).get('name', 'Unknown')})")

    print("\n📜 Últimas transacciones:")
    for tx in report['transactions']:
        value = float(Web3.fromWei(int(tx['value']), 'ether'))
        print(f" - [{tx['timeStamp']}] {tx['hash'][:10]}... ({value} ETH)")

    if args.output:
        filename = f"report_{report['address'][:8]}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Reporte guardado como {filename}")

if __name__ == "__main__":
    main()
