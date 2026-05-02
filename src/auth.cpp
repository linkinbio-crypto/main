#include "auth.h"
#include "http.h"
#include <iostream>
#include <regex>
#include <Windows.h>

// Change to your actual server URL
static const std::string SERVER = "https://yourserver.com";
static const std::string VERSION = "1.0";

bool Auth::ValidKeyFormat(const std::string& key) {
    std::regex pattern(R"(APB-(STD|PRO)-[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6})");
    return std::regex_match(key, pattern);
}

Auth::Result Auth::Validate(const std::string& key, const std::string& hwid) {
    auto response = HTTP::Post(SERVER + "/auth", {
        {"key",     key    },
        {"hwid",    hwid   },
        {"version", VERSION}
    });

    // Server unreachable
    if (response.contains("error"))
        return Result::SERVER_ERROR;

    // Not valid
    if (!response["valid"].get<bool>()) {
        std::string reason = response.value("reason", "UNKNOWN");

        if (reason == "EXPIRED")        return Result::EXPIRED;
        if (reason == "HWID_MISMATCH")  return Result::HWID_MISMATCH;
        if (reason == "BANNED")         return Result::BANNED;
        if (reason == "OUTDATED")       return Result::OUTDATED;
        return Result::INVALID;
    }

    return Result::OK;
}

void Auth::ShowResult(Result result) {
    switch (result) {
        case Result::EXPIRED:
            std::cout << "[!] Your key has expired. Renew in Discord.\n";
            break;
        case Result::HWID_MISMATCH:
            std::cout << "[!] HWID mismatch. Request a reset in Discord.\n";
            break;
        case Result::BANNED:
            std::cout << "[!] Your key has been banned.\n";
            break;
        case Result::OUTDATED:
            std::cout << "[!] Outdated version. Download latest in Discord.\n";
            break;
        case Result::SERVER_ERROR:
            std::cout << "[!] Could not reach auth server. Check your internet.\n";
            break;
        default:
            std::cout << "[!] Invalid key.\n";
            break;
    }
    Sleep(3000);
}
