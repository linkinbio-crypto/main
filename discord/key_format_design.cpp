// Format: PRODUCT-TIER-XXXXXX-XXXXXX-XXXXXX-CHECKSUM
// Example: APB-PRO-A3F9K2-7HN2P1-X9K3M4-C7

// Tiers
// APB-TRI = trial
// APB-STD = standard  
// APB-PRO = pro

std::string GenerateKey(const std::string& tier) {
    auto randomSegment = [](int len) {
        const std::string chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        // removed confusing chars: 0,O,1,I
        std::string out;
        for (int i = 0; i < len; i++)
            out += chars[rand() % chars.size()];
        return out;
    };

    std::string key = "APB-" + tier + "-"
        + randomSegment(6) + "-"
        + randomSegment(6) + "-"
        + randomSegment(6);

    // Append checksum so client can reject fakes instantly
    key += "-" + ComputeChecksum(key);
    return key;
}
