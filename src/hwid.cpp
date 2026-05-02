#include "hwid.h"
#include "utils.h"
#include <Windows.h>
#include <intrin.h>
#include <iphlpapi.h>
#include <sstream>

std::string HWID::Get() {
    std::stringstream ss;

    // CPU ID
    int cpu[4] = {};
    __cpuid(cpu, 0);
    ss << cpu[0] << cpu[1] << cpu[2] << cpu[3];

    // MAC address
    IP_ADAPTER_INFO adapters[16];
    DWORD bufLen = sizeof(adapters);
    if (GetAdaptersInfo(adapters, &bufLen) == ERROR_SUCCESS) {
        for (int i = 0; i < 6; i++)
            ss << (int)adapters[0].Address[i];
    }

    // Volume serial
    DWORD serial = 0;
    GetVolumeInformationA("C:\\", nullptr, 0, &serial,
        nullptr, nullptr, nullptr, 0);
    ss << serial;

    // Username
    char username[256];
    DWORD uLen = sizeof(username);
    GetUserNameA(username, &uLen);
    ss << username;

    return Utils::SHA256(ss.str());
}
