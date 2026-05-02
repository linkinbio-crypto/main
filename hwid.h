#pragma once
#include <string>
#include <vector>
#include <Windows.h>

namespace Utils {
    std::string SHA256(const std::string& input);
    std::string ToHex(const std::vector<unsigned char>& data);
    std::string GenerateKey(const std::string& tier);
    void        ClearConsole();
    void        PrintBanner();
}
