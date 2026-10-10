#pragma once
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
#include <cctype>
#include <cstdlib>
#include <random>
#include "Utility/MiniJson.hpp"
#include "constants.hpp"
// ─────────────────────────────────────────────
// get_col_data
// Reads a single reel strip from one Excel column (1-based col index).
// Skips null/empty cells, starts from row 2 (row index 1 in 0-based).
// ─────────────────────────────────────────────
namespace ReelFunctions {

    inline void get_reel_data(const char* sheetName, const char* jsonFilePath,
                          std::vector<std::vector<GameSymbols>>& reel,
                          int cols, int startCol = 0, int reelsetIndex = 0)
    {
        if (!jsonFilePath || jsonFilePath[0] == '\0')
            throw std::invalid_argument("get_reel_data: jsonFilePath is null or empty");
        if (!sheetName || sheetName[0] == '\0')
            throw std::invalid_argument("get_reel_data: sheetName is null or empty");

        // ---- read file ----
        std::ifstream file(jsonFilePath, std::ios::binary);
        if (!file.is_open())
            throw std::runtime_error("get_reel_data: failed to open '" + std::string(jsonFilePath) + "'");

        std::stringstream ss;
        ss << file.rdbuf();
        const std::string text = ss.str();

        // ---- parse ----
        MiniJson::Value root;
        try {
            root = MiniJson::Parser(text).parse();
        }
        catch (const std::exception& e) {
            throw std::runtime_error("get_reel_data: failed to parse '" + std::string(jsonFilePath) + "' — " + e.what());
        }

        if (!root.isObject())
            throw std::runtime_error("get_reel_data: root of '" + std::string(jsonFilePath) + "' must be an object");

        // ---- sheet -> reelsets ----
        const MiniJson::Value* sheet = root.find(sheetName);
        if (!sheet)
            throw std::runtime_error("get_reel_data: sheet '" + std::string(sheetName) + "' not found");
        if (!sheet->isArray())
            throw std::runtime_error("get_reel_data: sheet '" + std::string(sheetName) + "' must be an array of reelsets");

        // ---- pick reelset ----
        if (reelsetIndex < 0 || static_cast<size_t>(reelsetIndex) >= sheet->arr.size())
            throw std::out_of_range("get_reel_data: reelsetIndex " + std::to_string(reelsetIndex) +
                                    " out of range (sheet has " + std::to_string(sheet->arr.size()) + " reelsets)");

        const MiniJson::Value& reelSet = sheet->arr[reelsetIndex];
        if (!reelSet.isArray())
            throw std::runtime_error("get_reel_data: reelset must be a list of lists");

        if (startCol < 0 || cols < 0 || static_cast<size_t>(startCol + cols) > reelSet.arr.size())
            throw std::out_of_range("get_reel_data: requested columns exceed reelset size");

        // ---- read reels ----
        reel.clear();
        reel.resize(cols);

        for (int col = startCol; col < startCol + cols; ++col) {
            const MiniJson::Value& jReel = reelSet.arr[col];
            if (!jReel.isArray())
                throw std::runtime_error("get_reel_data: reel " + std::to_string(col) + " must be an array");

            auto& out = reel[col - startCol];
            out.reserve(jReel.arr.size());

            for (const MiniJson::Value& cell : jReel.arr) {
                if (!cell.isString() && !cell.isNumber())
                    continue;                                   // null / bool / nested -> skip

                GameSymbols sym = Constants::gameSymbolFromString(cell.str.c_str());
                if (sym == GameSymbols::Invalid)
                    continue;                                   // skip unknown symbols, as before

                out.push_back(sym);
            }
        }
    }

    struct Xoshiro256ss {
        uint64_t s[4];
        static uint64_t splitmix(uint64_t& x) {
            uint64_t z = (x += 0x9E3779B97F4A7C15ULL);
            z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
            z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
            return z ^ (z >> 31);
        }
        explicit Xoshiro256ss(uint64_t seed) { for (auto& v : s) v = splitmix(seed); }
        static inline uint64_t rotl(uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }
        inline uint64_t next() {
            const uint64_t result = rotl(s[1] * 5, 7) * 9;
            const uint64_t t = s[1] << 17;
            s[2] ^= s[0]; s[3] ^= s[1]; s[1] ^= s[2]; s[0] ^= s[3];
            s[2] ^= t; s[3] = rotl(s[3], 45);
            return result;
        }
        // uniform in [0, n), no division; bias is ~n/2^32, negligible for n = 50
        inline uint32_t bounded(uint32_t n) {
            return (uint32_t)(((next() >> 32) * (uint64_t)n) >> 32);
        }
    };

    // generate_slot_matrix
    // Picks a random window of matrixRows symbols from each reel,
    // then transposes from [col][row] to [row][col].
    // ─────────────────────────────────────────────
    inline void generate_slot_matrix(const std::vector<std::vector<GameSymbols>>& reelsVector,
                                 const int matrixSize[2],
                                 std::vector<std::vector<GameSymbols>>& matrix)
    {
        thread_local Xoshiro256ss rngTL(std::random_device{}());
        Xoshiro256ss& rng = rngTL;               // one thread_local access per call

        const int rows = matrixSize[0], cols = matrixSize[1];
        for (int col = 0; col < cols; ++col) {
            const auto& reel = reelsVector[col];
            const uint32_t n = (uint32_t)reel.size();
            uint32_t idx = rng.bounded(n);
            for (int row = 0; row < rows; ++row) {
                matrix[row][col] = reel[idx];
                if (++idx == n) idx = 0;
            }
        }
    }

    inline GameSymbols get_random_from_Col(const int colIndex,
        const std::vector<std::vector<GameSymbols>>& reelsVector) {
        thread_local std::mt19937 rng(std::random_device{}());
        const std::vector<GameSymbols>& reel = (reelsVector)[colIndex];

        std::uniform_int_distribution<int> dist(0, reel.size() - 1);
        

        return reel[dist(rng)];
    }
}