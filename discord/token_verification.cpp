#include <openssl/rsa.h>
#include <openssl/pem.h>

struct AuthToken {
    std::string key;
    std::string hwid;
    std::string tier;
    time_t      expiresAt;
};

// Verify JWT signature using server's public key
// Private key never leaves your server
AuthToken VerifyToken(const std::string& token) {
    // Split JWT: header.payload.signature
    auto parts = Split(token, '.');
    if (parts.size() != 3) throw std::runtime_error("Bad token");
    
    std::string toVerify = parts[0] + "." + parts[1];
    std::string sig      = Base64Decode(parts[2]);
    
    // Verify signature with embedded public key
    RSA* pubKey = LoadPublicKey(xorstr(PUBLIC_KEY_PEM));
    bool valid  = RSA_verify(toVerify, sig, pubKey);
    RSA_free(pubKey);
    
    if (!valid) throw std::runtime_error("Invalid signature");
    
    // Parse payload
    std::string payload = Base64Decode(parts[1]);
    return ParsePayload(payload); // json parse into AuthToken
}

// Full auth flow
bool Authenticate(const std::string& key) {
    std::string hwid = GetHWID();
    
    // Hit your server
    std::string response = HttpPost("https://yourserver.com/auth", {
        {"key",     key    },
        {"hwid",    hwid   },
        {"version", VERSION}
    });
    
    auto json = ParseJson(response);
    if (!json["valid"]) {
        ShowError(json["reason"]); // "EXPIRED", "BANNED", etc
        return false;
    }
    
    // Verify the token locally
    try {
        AuthToken token = VerifyToken(json["token"]);
        
        // Double check HWID matches what we sent
        if (token.hwid != hwid) return false;
        
        // Store token for re-verification without hitting server
        g_token = token;
        return true;
        
    } catch (...) {
        return false;
    }
}
