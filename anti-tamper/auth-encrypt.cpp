// XOR encrypt your shellcode/function bytes
void XorBuffer(BYTE* buf, size_t size, BYTE key) {
    for (size_t i = 0; i < size; i++)
        buf[i] ^= key;
}

void RunEncryptedAuth() {
    // Copy encrypted auth bytes
    std::vector<BYTE> code(encryptedAuth, encryptedAuth + sizeof(encryptedAuth));
    
    // Decrypt in memory
    XorBuffer(code.data(), code.size(), 0xAB);
    
    // Allocate RWX memory and run
    BYTE* exec = (BYTE*)VirtualAlloc(nullptr, code.size(), MEM_COMMIT, PAGE_EXECUTE_READWRITE);
    memcpy(exec, code.data(), code.size());
    
    ((void(*)())exec)(); // call it
    
    // Wipe immediately after
    memset(exec, 0, code.size());
    VirtualFree(exec, 0, MEM_RELEASE);
}
