void AntiTamperThread() {
    while (true) {
        // Randomize interval so it can't be timed/predicted
        std::this_thread::sleep_for(
            std::chrono::milliseconds(2000 + rand() % 3000)
        );
        
        if (AnyDebuggerDetected()) {
            g_tampered = true;
        }
        if (IsHooked((void*)&YourAuthFunction)) {
            g_tampered = true;
        }
    }
}

// Launch on startup
std::thread(AntiTamperThread).detach();
