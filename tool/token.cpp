// Client verifies token locally after first auth
bool VerifyToken(const std::string& token, const std::string& pubKey) {
    // Use OpenSSL or mbedTLS
    // RSA or ECDSA verify the server's signature
    // If valid, trust the expiry inside the token
    return RSA_verify(token, pubKey);
}
