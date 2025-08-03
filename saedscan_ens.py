import requests
from web3 import Web3
import os

# Configuraciones
INFURA_URL = "https://mainnet.infura.io/v3/TU_INFURA_KEY"
ETHERSCAN_API_KEY = "TU_ETHERSCAN_API_KEY"
OPENSEA_API_URL = "https://api.opensea.io/api/v1/assets"

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

def obtener_direccion_desde_ens(ens_name):
    try:
        address = w3.ens.address(ens_name)
        return address
    except Exception as e:
        print(f"[!] Error al resolver ENS: {e}")
        return None

def obtener_saldo_wallet(address):
    try:
        balance = w3.eth.get_balance(address)
        return w3.fromWei(balance, 'ether')
    except Exception as e:
        print(f"[!] Error al obtener saldo: {e}")
        return None

def obtener_transacciones_wallet(address):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    try:
        data = response.json()
        if data['status'] == '1':
            return data['result']
        else:
            return []
    except:
        return []

def obtener_nfts_wallet(address):
    params = {
        'owner': address,
        'order_direction': 'desc',
        'offset': 0,
        'limit': 10
    }
    try:
        response = requests.get(OPENSEA_API_URL, params=params)
        return response.json().get("assets", [])
    except Exception as e:
        print(f"[!] Error al obtener NFTs: {e}")
        return []

if __name__ == "__main__":
    ens_name = input("🔍 Introduce ENS o dirección Ethereum: ")
    if ens_name.endswith(".eth"):
        wallet_address = obtener_direccion_desde_ens(ens_name)
    else:
        wallet_address = ens_name

    if wallet_address:
        print(f"\n📍 Dirección detectada: {wallet_address}")
        saldo = obtener_saldo_wallet(wallet_address)
        print(f"💰 Saldo: {saldo} ETH")

        print("\n📦 NFTS:")
        nfts = obtener_nfts_wallet(wallet_address)
        for nft in nfts:
            print(f" - {nft['name']} ({nft['token_id']}) en {nft['collection']['name']}")

        print("\n📈 Últimas transacciones:")
        txs = obtener_transacciones_wallet(wallet_address)
        for tx in txs[:5]:
            print(f" - Hash: {tx['hash'][:10]}... Valor: {w3.fromWei(int(tx['value']), 'ether')} ETH")
    else:
        print("[X] Dirección no válida o no encontrada.")
