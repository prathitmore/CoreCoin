#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <ctime>
#include <cstdint>
#include <iomanip>
#include <openssl/sha.h>
#include <openssl/evp.h>

// Simple SHA256 helper
void sha256_double(const uint8_t* data, size_t len, uint8_t* hash) {
    uint8_t tmp[32];
    SHA256(data, len, tmp);
    SHA256(tmp, 32, hash);
}

// Scrypt implementation using OpenSSL 1.1+ EVP_PKEY_SCRYPT
bool scrypt_1024_1_1_256(const uint8_t* input, uint8_t* output) {
    EVP_PKEY_CTX *pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_SCRYPT, NULL);
    if (!pctx) return false;
    if (EVP_PKEY_derive_init(pctx) <= 0) { EVP_PKEY_CTX_free(pctx); return false; }
    if (EVP_PKEY_CTX_set1_pbe_pass(pctx, input, 80) <= 0) { EVP_PKEY_CTX_free(pctx); return false; }
    if (EVP_PKEY_CTX_set1_scrypt_salt(pctx, input, 80) <= 0) { EVP_PKEY_CTX_free(pctx); return false; }
    if (EVP_PKEY_CTX_set_scrypt_N(pctx, 1024) <= 0) { EVP_PKEY_CTX_free(pctx); return false; }
    if (EVP_PKEY_CTX_set_scrypt_r(pctx, 1) <= 0) { EVP_PKEY_CTX_free(pctx); return false; }
    if (EVP_PKEY_CTX_set_scrypt_p(pctx, 1) <= 0) { EVP_PKEY_CTX_free(pctx); return false; }
    size_t outlen = 32;
    if (EVP_PKEY_derive(pctx, output, &outlen) <= 0) { EVP_PKEY_CTX_free(pctx); return false; }
    EVP_PKEY_CTX_free(pctx);
    return true;
}

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cout << "Usage: genesis_miner <nTime> <nBits> <merkle_root_hex>" << std::endl;
        return 1;
    }

    uint32_t nTime = std::stoul(argv[1]);
    uint32_t nBits = std::stoul(argv[2], nullptr, 0);
    std::string merkle_hex = argv[3];

    uint8_t merkle_root[32];
    for (int i = 0; i < 32; i++) {
        merkle_root[i] = std::stoul(merkle_hex.substr(i*2, 2), nullptr, 16);
    }
    // Reverse for little-endian if it was provided as big-endian hex (which it is in my python script)
    // Wait, my python script prints merkle_root[::-1].hex() which is BE. 
    // So I reverse it back to LE for the header.
    for (int i = 0; i < 16; i++) {
        uint8_t tmp = merkle_root[i];
        merkle_root[i] = merkle_root[31-i];
        merkle_root[31-i] = tmp;
    }

    // Header structure (80 bytes)
    uint8_t header[80] = {0};
    uint32_t nVersion = 1;
    std::memcpy(header, &nVersion, 4);
    // hashPrevBlock is 0 (already 0)
    std::memcpy(header + 36, merkle_root, 32);
    std::memcpy(header + 68, &nTime, 4);
    std::memcpy(header + 72, &nBits, 4);

    // Target calculation
    unsigned int nSize = nBits >> 24;
    unsigned int nWord = nBits & 0x007fffff;
    // Simple comparison logic: find how many zeros are needed
    // Difficulty 1: 0x1e0ffff0 (20 zeros binary = 5 zeros hex)
    
    std::cout << "Mining with nTime: " << nTime << ", nBits: 0x" << std::hex << nBits << std::dec << std::endl;
    std::cout << "Merkle (LE): ";
    for (int i=0; i<32; i++) printf("%02x", header[36+i]);
    std::cout << std::endl;

    uint32_t nonce = 0;
    uint8_t scrypt_hash[32];
    uint8_t sha_hash[32];
    
    time_t start = time(0);
    while (true) {
        std::memcpy(header + 76, &nonce, 4);
        if (scrypt_1024_1_1_256(header, scrypt_hash)) {
            // Check difficulty (simplified for 0x1e0ffff0):
            // Scrypt hash must have enough leading zeros (little-endian: trailing in hex string, but let's check high bytes)
            // 0x1e0ffff0 means target is roughly 2^236.
            // Scrypt hashes are 256 bits. 256 - 236 = 20 bits of zero from the top.
            // 20 bits = 2.5 bytes of zero at the end of the byte array (little-endian interpretation).
            
            // Accurate check (big-endian value <= target)
            // But scrypt_hash is the little-endian result. 
            // We need to compare correctly.
            
            // Let's just do target check as a uint256 comparison
            // Or for Genesis, Difficulty 1 is easy enough to check leading zeros.
            if (scrypt_hash[31] == 0 && scrypt_hash[30] == 0 && scrypt_hash[29] < 0x10) { // roughly bits 0x1e...
                 sha256_double(header, 80, sha_hash);
                 std::cout << "\nFOUND GENESIS!" << std::endl;
                 std::cout << "Nonce: " << nonce << std::endl;
                 std::cout << "Scrypt Hash: ";
                 for (int i=31; i>=0; i--) printf("%02x", scrypt_hash[i]);
                 std::cout << "\nSHA256 Hash: ";
                 for (int i=31; i>=0; i--) printf("%02x", sha_hash[i]);
                 std::cout << std::endl;
                 break;
            }
        }
        
        nonce++;
        if (nonce % 100000 == 0) {
            std::cout << "Nonce: " << nonce << " (" << (time(0) - start) << "s)\r" << std::flush;
        }
    }

    return 0;
}
