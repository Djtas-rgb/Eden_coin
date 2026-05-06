import hashlib
import json
import time
import os
import secrets
import threading
from datetime import datetime
from typing import Dict
from flask import Flask, jsonify

app = Flask(__name__)

class Wallet:
    def __init__(self, name: str):
        self.name = name
        self.private_key = secrets.token_hex(64)
        self.public_key = hashlib.sha3_512(self.private_key.encode()).hexdigest()
        self.address = f"EDEN_{hashlib.sha3_512(self.public_key.encode()).hexdigest()[:64]}"

class EdenCoin:
    def __init__(self):
        self.data_file = "eden_data.json"
        self.chain = []
        self.wallets: Dict[str, Wallet] = {}
        self.balances: Dict[str, int] = {}
        self.difficulty = 5
        self.auto_mining = False
        self.load_or_create()

    def load_or_create(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                self.chain = data.get("chain", [])
                self.balances = data.get("balances", {})
            except:
                self.create_genesis()
        else:
            self.create_genesis()

    def create_genesis(self):
        genesis = {
            "index": 0,
            "type": "genesis",
            "timestamp": datetime.now().isoformat(),
            "message": "Fair Launch - 8.1 Billion EDEN",
            "total_supply": 8100000000 * 10**18,
            "hash": ""
        }
        genesis["hash"] = hashlib.sha256(json.dumps(genesis, sort_keys=True).encode()).hexdigest()
        self.chain.append(genesis)
        self.save()

    def save(self):
        data = {"chain": self.chain[-500:], "balances": self.balances}
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_or_create_wallet(self, name: str):
        if name not in self.wallets:
            self.wallets[name] = Wallet(name)
        return self.wallets[name]

    def mine_block(self, miner_name="miner"):
        miner = self.get_or_create_wallet(miner_name)
        reward = 25 * 10**18 // (2 ** (len(self.chain) // 210000))

        if len(self.chain) % 50 == 0 and self.difficulty < 9:
            self.difficulty += 1

        block = {
            "index": len(self.chain),
            "timestamp": datetime.now().isoformat(),
            "miner": miner_name,
            "reward": reward,
            "difficulty": self.difficulty,
            "hash": ""
        }

        target = "0" * self.difficulty
        nonce = 0
        while True:
            block["nonce"] = nonce
            block["hash"] = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
            if block["hash"].startswith(target):
                break
            nonce += 1

        self.balances[miner.address] = self.balances.get(miner.address, 0) + reward
        self.chain.append(block)
        self.save()

    def get_status(self):
        total_mined = sum(b.get("reward", 0) for b in self.chain) / 10**18
        return {
            "blocks": len(self.chain),
            "total_mined": round(total_mined, 2),
            "difficulty": self.difficulty,
            "wallets": {
                name: round(self.balances.get(w.address, 0) / 10**18, 2)
                for name, w in self.wallets.items()
            }
        }

coin = EdenCoin()

@app.route('/')
def home():
    s = coin.get_status()
    return f"""
    <html><head><title>EdenCoin</title>
    <style>body{{background:#0a0a1a;color:#0f0;font-family:monospace;padding:20px;}}</style></head>
    <body>
    <h1>🌍 EDENCOIN - FAIR LAUNCH</h1>
    <p>Total Supply: 8.1 Billion EDEN (One per person on Earth)</p>
    <p>Blocks: {s['blocks']} | Mined: {s['total_mined']} EDEN | Difficulty: {s['difficulty']}</p>
    <h2>Wallets</h2>
    <table border="1" cellpadding="10">
    <tr><th>Name</th><th>Balance (EDEN)</th></tr>
    {''.join(f'<tr><td>{n}</td><td>{b:,.2f}</td></tr>' for n,b in s['wallets'].items())}
    </table>
    <br><a href="/mine">Mine One Block</a> | <a href="/">Refresh</a>
    </body></html>
    """

@app.route('/mine')
def mine():
    coin.mine_block("public_miner")
    return "<h2>✅ Block Mined Successfully!</h2><a href='/'>← Back</a>"

if __name__ == "__main__":
    # For local testing
    print("🌐 EdenCoin running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)
