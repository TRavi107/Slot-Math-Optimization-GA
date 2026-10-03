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

    // generate_slot_matrix
    // Picks a random window of matrixRows symbols from each reel,
    // then transposes from [col][row] to [row][col].
    // ─────────────────────────────────────────────
    inline void generate_slot_matrix(const std::vector<std::vector<GameSymbols>> reelsVector, const int matrixSize[2], std::vector<std::vector<GameSymbols>>& matrix) {
        // Select the correct reel set

        // Thread-local RNG — safe for multi-threaded simulation
        thread_local std::mt19937 rng(std::random_device{}());

        for (int col = 0; col < matrixSize[1]; ++col) {
            const std::vector<GameSymbols>& reel = (reelsVector)[col];

            std::uniform_int_distribution<int> dist(0, reel.size() - 1);
            int startIdx = dist(rng);

            for (int row = 0; row < matrixSize[0]; row++)
                matrix[row][col] = reel[(startIdx + row) % reel.size()];
        }

    }

    inline GameSymbols get_random_from_Col(const int colIndex, const std::vector<std::vector<GameSymbols>> reelsVector) {
        thread_local std::mt19937 rng(std::random_device{}());
        const std::vector<GameSymbols>& reel = (reelsVector)[colIndex];

        std::uniform_int_distribution<int> dist(0, reel.size() - 1);
        

        return reel[dist(rng)];
    }
}