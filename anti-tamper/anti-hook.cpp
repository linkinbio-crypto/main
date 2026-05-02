bool IsHooked(void* func) {
    BYTE* bytes = (BYTE*)func;
    // JMP hook signature: E9 ?? ?? ?? ??
    // or MOV RAX + JMP RAX: 48 B8 ... FF E0
    return bytes[0] == 0xE9
        || bytes[0] == 0xEB
        || (bytes[0] == 0xFF && bytes[1] == 0x25)
        || (bytes[0] == 0x48 && bytes[1] == 0xB8);
}

void CheckAuthIntegrity() {
    if (IsHooked((void*)&YourAuthFunction)) {
        ExitProcess(0);
    }
}
