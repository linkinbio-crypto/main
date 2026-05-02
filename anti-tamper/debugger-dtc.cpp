bool IsDebuggerPresent_PEB() {
    // Read PEB directly — harder to fake than IsDebuggerPresent()
    PPEB peb = (PPEB)__readgsqword(0x60);
    return peb->BeingDebugged;
}

bool IsDebuggerPresent_Heap() {
    // Heap flags are set differently under a debugger
    PPEB peb = (PPEB)__readgsqword(0x60);
    PVOID heap = peb->ProcessHeap;
    DWORD flags   = *(DWORD*)((BYTE*)heap + 0x70);
    DWORD forceFlags = *(DWORD*)((BYTE*)heap + 0x74);
    return (flags & 0x50) || (forceFlags != 0);
}

bool IsDebuggerPresent_Timing() {
    // Debuggers slow execution — detect via RDTSC timing
    UINT64 start = __rdtsc();
    // do some dummy work
    volatile int x = 0;
    for (int i = 0; i < 1000; i++) x += i;
    UINT64 end = __rdtsc();
    return (end - start) > 500000; // tuned threshold
}

bool IsDebuggerPresent_Hardware() {
    CONTEXT ctx = {};
    ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
    GetThreadContext(GetCurrentThread(), &ctx);
    // Hardware breakpoints set Dr0-Dr3
    return ctx.Dr0 || ctx.Dr1 || ctx.Dr2 || ctx.Dr3;
}

bool IsDebuggerPresent_Exception() {
    __try {
        __debugbreak(); // INT3
        return true;    // debugger caught it
    } __except(EXCEPTION_EXECUTE_HANDLER) {
        return false;   // no debugger, exception propagated normally
    }
}

// Run all checks together
bool AnyDebuggerDetected() {
    return IsDebuggerPresent_PEB()
        || IsDebuggerPresent_Heap()
        || IsDebuggerPresent_Timing()
        || IsDebuggerPresent_Hardware()
        || IsDebuggerPresent_Exception()
        || IsDebuggerPresent(); // Win32 baseline
}
