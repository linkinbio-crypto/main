#include <intrin.h>
#include <iphlpapi.h>

std::string GetHWID() {
    // Combine multiple hardware identifiers
    std::string hwid = "";
    
    // CPU ID
    int cpuInfo[4];
    __cpuid(cpuInfo, 0);
    hwid += std::to_string(cpuInfo[0]) + cpuInfo[1] + cpuInfo[2] + cpuInfo[3];
    
    // MAC address
    IP_ADAPTER_INFO adapterInfo[16];
    DWORD bufLen = sizeof(adapterInfo);
    if (GetAdaptersInfo(adapterInfo, &bufLen) == ERROR_SUCCESS) {
        for (int i = 0; i < 6; i++)
            hwid += std::to_string(adapterInfo[0].Address[i]);
    }
    
    // Hash it so raw hardware info isn't sent
    return SHA256(hwid);
}
