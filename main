#include "utils.h"
#include <openssl/sha.h>
#include <sstream>
#include <iomanip>
#include <random>

std::string Utils::SHA256(const std::string& input) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    ::SHA256((unsigned char*)input.c_str(), input.size(), hash);

    std::stringstream ss;
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++)
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    return ss.str();
}

std::string Utils::ToHex(const std::vector<unsigned char>& data) {
    std::stringstream ss;
    for (auto b : data)
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)b;
    return ss.str();
}

void Utils::ClearConsole() {
    system("cls");
}

void Utils::PrintBanner() {
    std::cout << R"(
    ___    ____  ____                  __
   /   |  / __ \/ __ )________  ____  / /_____  _____
  / /| | / /_/ / __  / ___/ _ \/ __ \/ //_/ _ \/ ___/
 / ___ |/ ____/ /_/ / /  /  __/ /_/ / ,< /  __/ /
/_/  |_/_/   /_____/_/   \___/\__,_/_/|_|\___/_/

    )" << "\n";
    std::cout << "    Version 1.0  |  discord.gg/yourserver\n\n";
}
