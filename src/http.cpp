#include "http.h"
#include <curl/curl.h>

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* out) {
    out->append((char*)contents, size * nmemb);
    return size * nmemb;
}

static std::string DoRequest(const std::string& url, const std::string* postData = nullptr) {
    CURL* curl = curl_easy_init();
    std::string response;

    if (!curl) return "";

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL,            url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER,     headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION,  WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA,      &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT,        10L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);

    if (postData) {
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData->c_str());
    }

    CURLcode res = curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) return "";
    return response;
}

nlohmann::json HTTP::Post(const std::string& url, const nlohmann::json& body) {
    std::string payload = body.dump();
    std::string response = DoRequest(url, &payload);
    if (response.empty()) return { {"error", "no_response"} };
    try { return nlohmann::json::parse(response); }
    catch (...) { return { {"error", "parse_failed"} }; }
}

nlohmann::json HTTP::Get(const std::string& url) {
    std::string response = DoRequest(url);
    if (response.empty()) return { {"error", "no_response"} };
    try { return nlohmann::json::parse(response); }
    catch (...) { return { {"error", "parse_failed"} }; }
}
