import hashlib
import struct
import time
import multiprocessing as mp
import sys

def sha256_double(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def calculate_merkle_root(pszTimestamp, reward):
    scriptSig = b'\x04\xff\xff\x00\x1d\x01\x04' 
    psz_bytes = pszTimestamp.encode('utf-8')
    scriptSig += bytes([len(psz_bytes)]) + psz_bytes
    
    tx = struct.pack('<i', 1) 
    tx += b'\x01' 
    tx += b'\x00' * 32 
    tx += b'\xff\xff\xff\xff' 
    tx += bytes([len(scriptSig)])
    tx += scriptSig
    tx += b'\xff\xff\xff\xff' 
    tx += b'\x01' 
    tx += struct.pack('<q', reward * 100000000) 
    
    pubkey = bytes.fromhex('040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9')
    scriptPubKey = b'\x41' + pubkey + b'\xac' 
    tx += bytes([len(scriptPubKey)])
    tx += scriptPubKey
    tx += b'\x00' * 4 
    
    return sha256_double(tx)

def miner_worker(name, header_base, target, start_nonce, end_nonce, result_queue):
    nonce = start_nonce
    while nonce < end_nonce:
        header = header_base + struct.pack('<I', nonce)
        pow_hash = hashlib.scrypt(header, salt=header, n=1024, r=1, p=1, dklen=32)
        if int.from_bytes(pow_hash, 'little') <= target:
            sha_hash = sha256_double(header)
            result_queue.put((nonce, sha_hash[::-1].hex(), pow_hash[::-1].hex()))
            return
        nonce += 1
    return

def mine_genesis_fast(name, nTime, nBits, pszTimestamp, reward):
    print(f"\n--- MINING {name} ---")
    sys.stdout.flush()
    merkle_root = calculate_merkle_root(pszTimestamp, reward)
    target = (nBits & 0xffffff) * 2**(8 * ((nBits >> 24) - 3))
    
    nVersion = 1
    hashPrevBlock = b'\x00' * 32
    header_base = struct.pack('<i', nVersion) + hashPrevBlock + merkle_root + struct.pack('<I', nTime) + struct.pack('<I', nBits)
    
    num_procs = mp.cpu_count()
    chunk_size = 10000 # very small for feedback
    result_queue = mp.Queue()
    
    found = False
    base_nonce = 0
    start_time = time.time()
    
    while not found:
        procs = []
        for i in range(num_procs):
            p = mp.Process(target=miner_worker, args=(name, header_base, target, base_nonce + i*chunk_size, base_nonce + (i+1)*chunk_size, result_queue))
            procs.append(p)
            p.start()
        
        while any(p.is_alive() for p in procs):
            if not result_queue.empty():
                found_res = result_queue.get()
                for p in procs: p.terminate()
                found = True
                break
            time.sleep(1)
        
        if found:
            nonce, sha_hash, pow_hash = found_res
            print(f"Name: {name}\nTimestamp: {nTime}\nNonce: {nonce}\nBits: 0x{nBits:08x}\nMerkle Root: {merkle_root[::-1].hex()}\nGenesis Hash (SHA256): {sha_hash}\nGenesis Hash (Scrypt): {pow_hash}\nTotal time: {time.time() - start_time:.2f}s")
            sys.stdout.flush()
            return found_res
        
        base_nonce += num_procs * chunk_size
        print(f"  {name}: {base_nonce} nonces checked ({time.time() - start_time:.2f}s, rate: {base_nonce/(time.time()-start_time+0.0001):.1f}/s)")
        sys.stdout.flush()

if __name__ == "__main__":
    t = 1774947254
    msg = "Balance Over Power"
    mine_genesis_fast("Mainnet", t, 0x1e0ffff0, msg, 50)
    mine_genesis_fast("Testnet", t, 0x1e0ffff0, msg, 50)
    mine_genesis_fast("Regtest", t, 0x207fffff, msg, 50)
