import json
import urllib.request
from base64 import b64encode

# Minimal Block Explorer Configuration
RPC_URL = 'http://127.0.0.1:9776' # standard mainnet RPC port
RPC_USER = 'corecoinrpc'
RPC_PASS = 'corepass123'

def rpc_call(method, params=[]):
    payload = json.dumps({'method': method, 'params': params, 'id': 1}).encode()
    headers = {'Content-Type': 'application/json', 'Authorization': 'Basic ' + b64encode(f'{RPC_USER}:{RPC_PASS}'.encode()).decode()}
    req = urllib.request.Request(RPC_URL, data=payload, headers=headers)
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read())['result']
    except Exception as e:
        return f'RPC Error: {e}'

if __name__ == '__main__':
    print('=== CORECOIN TERMINAL EXPLORER ===')
    print('Fetching Network Info...')
    info = rpc_call('getblockchaininfo')
    if isinstance(info, dict):
        print(f'Total Blocks: {info.get("blocks")}')
        print(f'Difficulty: {info.get("difficulty")}')
        
        best_hash = info.get('bestblockhash')
        print(f'
--- LATEST BLOCK ({best_hash}) ---')
        block_data = rpc_call('getblock', [best_hash])
        if isinstance(block_data, dict):
            print(f'Mined At: {block_data.get("time")}')
            print(f'Size: {block_data.get("size")} bytes')
            print(f'Transactions ({len(block_data.get("tx", []))}):')
            for tx in block_data.get('tx', [])[:5]:
                print(f'  -> {tx}')
    else:
        print(info)
