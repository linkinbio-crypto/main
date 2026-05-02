#pragma once
#include <string>
#include <nlohmann/json.hpp>

namespace HTTP {
    nlohmann::json Post(const std::string& url, const nlohmann::json& body);
    nlohmann::json Get(const std::string& url);
}
