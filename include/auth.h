#pragma once
#include <string>

namespace Auth {
    enum class Result {
        OK,
        INVALID,
        EXPIRED,
        HWID_MISMATCH,
        BANNED,
        OUTDATED,
        SERVER_ERROR
    };

    bool   ValidKeyFormat(const std::string& key);
    Result Validate(const std::string& key, const std::string& hwid);
    void   ShowResult(Result result);
}
