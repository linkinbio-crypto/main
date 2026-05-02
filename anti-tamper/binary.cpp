#include <Windows.h>
#include <string>
#include <vector>

// Hash your own .text section (code section)
std::string HashOwnTextSection() {
    HMODULE base = GetModuleHandle(nullptr);
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)base;
    PIMAGE_NT_HEADERS nt  = (PIMAGE_NT_HEADERS)((BYTE*)base + dos->e_lfanew);
    
    PIMAGE_SECTION_HEADER section = IMAGE_FIRST_SECTION(nt);
    for (int i = 0; i < nt->FileHeader.NumberOfSections; i++, section++) {
        if (strcmp((char*)section->Name, ".text") == 0) {
            BYTE* start = (BYTE*)base + section->VirtualAddress;
            SIZE_T size  = section->Misc.VirtualSize;
            return SHA256(start, size); // your sha256 impl
        }
    }
    return "";
}

// At startup, compare against hash baked in at compile time
void VerifyIntegrity() {
    const std::string EXPECTED = "a3f1c9..."; // set this after final build
    if (HashOwnTextSection() != EXPECTED) {
        // Don't tell the user why — just silently exit or fake-run
        ExitProcess(0);
    }
}
