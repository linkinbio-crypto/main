void ErasePEHeader() {
    // Wipe the PE header from memory after loading
    // Makes it much harder to reconstruct the binary from a dump
    HMODULE base = GetModuleHandle(nullptr);
    DWORD oldProtect;
    VirtualProtect(base, 0x1000, PAGE_READWRITE, &oldProtect);
    memset(base, 0, 0x1000); // zero the header
    VirtualProtect(base, 0x1000, oldProtect, &oldProtect);
}

void CorruptDumpableRegions() {
    // Overwrite the SizeOfImage in the PE header clone
    // so dumpers calculate wrong boundaries
    HMODULE base = GetModuleHandle(nullptr);
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)base;
    PIMAGE_NT_HEADERS nt  = (PIMAGE_NT_HEADERS)((BYTE*)base + dos->e_lfanew);
    DWORD old;
    VirtualProtect(&nt->OptionalHeader.SizeOfImage, 4, PAGE_READWRITE, &old);
    nt->OptionalHeader.SizeOfImage = 0; // corrupt it
    VirtualProtect(&nt->OptionalHeader.SizeOfImage, 4, old, &old);
}
