import hashlib
import struct
import time

def sha256_double(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def calculate_merkle_root(pszTimestamp, reward):
    # nVersion = 1
    scriptSig = b'\x04\xff\xff\x00\x1d\x01\x04' # 0x1d00ffff, 4
    psz_bytes = pszTimestamp.encode('utf-8')
    # scriptSig: nBits, 4, len(psz), psz
    scriptSig += bytes([len(psz_bytes)]) + psz_bytes
    
    tx = struct.pack('<i', 1) # nVersion
    tx += b'\x01' # vin count
    tx += b'\x00' * 32 # prev hash
    tx += b'\xff\xff\xff\xff' # prev n
    tx += bytes([len(scriptSig)])
    tx += scriptSig
    tx += b'\xff\xff\xff\xff' # sequence
    
    tx += b'\x01' # vout count
    tx += struct.pack('<q', reward * 100000000) # nValue
    
    pubkey = bytes.fromhex('040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9')
    scriptPubKey = b'\x41' + pubkey + b'\xac' 
    
    tx += bytes([len(scriptPubKey)])
    tx += scriptPubKey
    tx += b'\x00' * 4 # locktime
    
    return sha256_double(tx)

def mine_genesis(name, nTime, nBits, pszTimestamp, reward):
    print(f"\n--- GENERATING GENESIS FOR: {name} ---")
    merkle_root = calculate_merkle_root(pszTimestamp, reward)
    
    target = (nBits & 0xffffff) * 2**(8 * ((nBits >> 24) - 3))
    
    nVersion = 1
    hashPrevBlock = b'\x00' * 32
    
    nonce = 0
    header_base = struct.pack('<i', nVersion) + hashPrevBlock + merkle_root + struct.pack('<I', nTime) + struct.pack('<I', nBits)
    
    while True:
        header = header_base + struct.pack('<I', nonce)
        pow_hash = hashlib.scrypt(header, salt=header, n=1024, r=1, p=1, dklen=32)
        pow_hash_val = int.from_bytes(pow_hash, 'little')
        
        if pow_hash_val <= target:
            sha_hash = sha256_double(header)
            
            print(f"Name: {name}")
            print(f"Timestamp: {nTime}")
            print(f"Phrase: {pszTimestamp}")
            print(f"Nonce: {nonce}")
            print(f"Bits: 0x{nBits:08x}")
            print(f"Merkle Root: {merkle_root[::-1].hex()}")
            print(f"Genesis Hash (SHA256): {sha_hash[::-1].hex()}")
            print(f"Genesis Hash (Scrypt PoW): {pow_hash[::-1].hex()}")
            return {
                'name': name,
                'timestamp': nTime,
                'nonce': nonce,
                'bits': f"0x{nBits:08x}",
                'merkle_root': merkle_root[::-1].hex(),
                'hash_sha': sha_hash[::-1].hex(),
                'hash_scrypt': pow_hash[::-1].hex()
            }
        
        nonce += 1
        if nonce % 200000 == 0:
            print(f" {name} progress: nonce {nonce}...", end='\r')

if __name__ == "__main__":
    t = 1774947254
    msg = "Balance Over Power"
    
    m = mine_genesis("Mainnet", t, 0x1e0ffff0, msg, 50)
    t = mine_genesis("Testnet", t, 0x1e0ffff0, msg, 50)
    r = mine_genesis("Regtest", t, 0x207fffff, msg, 50)
