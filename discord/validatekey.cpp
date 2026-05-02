std::string ComputeChecksum(const std::string& key) {
    // Simple but effective — HMAC the key with a secret
    // secret is obfuscated in binary (xorstr)
    std::string secret = xorstr("your_secret_salt_here");
    std::string raw = HMAC_SHA256(key, secret);
    
    // Return first 6 chars of hash as checksum segment
    return raw.substr(0, 6);
}

bool ValidKeyFormat(const std::string& key) {
    // Check structure before hitting server
    std::regex pattern(R"(APB-(TRI|STD|PRO)-[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6})");
    if (!std::regex_match(key, pattern)) return false;
    
    // Verify checksum segment
    std::string withoutChecksum = key.substr(0, key.size() - 7);
    std::string expectedChecksum = ComputeChecksum(withoutChecksum);
    std::string actualChecksum = key.substr(key.size() - 6);
    
    return expectedChecksum == actualChecksum;
}
