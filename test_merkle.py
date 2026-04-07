import hashlib
import struct

def sha256_double(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def calculate_merkle_root(pszTimestamp, reward):
    # nVersion = 1
    version = struct.pack('<i', 1)
    
    # scriptSig components - Replicating CScript() << 486604799 << CScriptNum(4) << psz
    # 486604799 is 0x1d00ffff. In Bitcoin Script, integers are pushed as data if they are larger than 16.
    # 0x1d00ffff -> little-endian is ffff001d. 
    # But wait, 0x1d00ffff is positive. 
    # Bitcoin script numbers are signed.
    # 0x1d00ffff -> 4 bytes: 0xf f f 0 0 1 d. 
    # Actually, 486604799 is usually pushed as 4 bytes: 0x04 0xff 0xff 0x00 0x1d.
    # No, CScript() << 486604799 usually pushes it.
    
    # Let's see the Litecoin genesis coinbase scriptSig hex:
    # 04ffff001d0104(length)(psz) -> this confirms:
    # 04 -> length 4, ffff001d -> value
    # 01 -> length 1, 04 -> value 4
    
    scriptSig = b'\x04\xff\xff\x00\x1d\x01\x04'
    psz_bytes = pszTimestamp.encode('utf-8')
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
    
    # scriptPubKey: length(65) + pubkey + OP_CHECKSIG
    # Litecoin uses: 040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9
    pubkey = bytes.fromhex('040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9')
    scriptPubKey = b'\x41' + pubkey + b'\xac' # 0x41 is length 65
    
    tx += bytes([len(scriptPubKey)])
    tx += scriptPubKey
    tx += b'\x00' * 4 # locktime
    
    return sha256_double(tx)

if __name__ == "__main__":
    ltc_psz = "NY Times 05/Oct/2011 Steve Jobs, Apple’s Visionary, Dies at 56"
    merkle = calculate_merkle_root(ltc_psz, 50)
    print(f"Merkle: {merkle[::-1].hex()}")
    # Expected for Litecoin: 97ddfbbae6be97fd6cdf3e7ca13232a3afff2353e29badfab7f73011edd4ced9
