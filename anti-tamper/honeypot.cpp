bool g_tampered = false;

void CheckAll() {
    if (AnyDebuggerDetected() || IsHooked(...) || !VerifyIntegrity()) {
        g_tampered = true; // don't exit yet
    }
}

void DoAPBreak() {
    if (g_tampered) {
        // Pretend to work — sleep fake delays, print fake logs
        // but actually do nothing
        // Confuses reverse engineers watching behavior
        std::this_thread::sleep_for(std::chrono::milliseconds(rand() % 50));
        return;
    }
    // real logic here
}
