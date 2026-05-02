#include <iostream>
#include <Windows.h>
#include "utils.h"
#include "hwid.h"
#include "auth.h"

void EnforceSingleInstance() {
    HANDLE mutex = CreateMutexA(nullptr, TRUE, "APBreaker_Mutex");
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        std::cout << "[!] Already running.\n";
        Sleep(1500);
        ExitProcess(0);
    }
}

int main() {
    EnforceSingleInstance();
    Utils::ClearConsole();
    Utils::PrintBanner();

    // Get HWID
    std::string hwid = HWID::Get();

    // Get key from user
    std::string key;
    std::cout << "  Enter key: ";
    std::cin >> key;
    std::cout << "\n";

    // Validate format locally first
    if (!Auth::ValidKeyFormat(key)) {
        std::cout << "[!] Invalid key format.\n";
        Sleep(2000);
        return 1;
    }

    // Hit server
    std::cout << "  Authenticating...\n";
    Auth::Result result = Auth::Validate(key, hwid);

    if (result != Auth::Result::OK) {
        Auth::ShowResult(result);
        return 1;
    }

    std::cout << "  [+] Authenticated successfully.\n\n";
    Sleep(1000);

    // ── placeholder until RPA is ready ──
    std::cout << "  [*] APBreaker running...\n";
    std::cout << "  [*] Press CTRL+C to stop.\n\n";

    while (true) {
        Sleep(1000);
    }

    return 0;
}
