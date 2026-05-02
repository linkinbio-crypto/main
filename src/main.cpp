#include <iostream>
#include "auth.h"
#include "hwid.h"

int main() {
    // Clear console, show banner
    system("cls");
    std::cout << "APBreaker v1.0\n";
    std::cout << "--------------\n\n";

    // Get key from user
    std::string key;
    std::cout << "Enter your key: ";
    std::cin >> key;

    // Validate format locally first before hitting server
    if (!Auth::ValidKeyFormat(key)) {
        std::cout << "[!] Invalid key format.\n";
        Sleep(2000);
        return 1;
    }

    // Get HWID
    std::string hwid = HWID::Get();

    // Hit your server
    Auth::Result result = Auth::Validate(key, hwid);

    switch (result) {
        case Auth::Result::OK:
            std::cout << "[+] Authenticated.\n";
            break;
        case Auth::Result::INVALID:
            std::cout << "[!] Invalid key.\n";
            Sleep(2000); return 1;
        case Auth::Result::EXPIRED:
            std::cout << "[!] Key expired.\n";
            Sleep(2000); return 1;
        case Auth::Result::HWID_MISMATCH:
            std::cout << "[!] HWID mismatch. Contact support.\n";
            Sleep(2000); return 1;
        case Auth::Result::BANNED:
            std::cout << "[!] Key banned.\n";
            Sleep(2000); return 1;
        case Auth::Result::SERVER_ERROR:
            std::cout << "[!] Could not reach auth server.\n";
            Sleep(2000); return 1;
    }

    // Auth passed — launch the actual tool
    Launch();
    return 0;
}
