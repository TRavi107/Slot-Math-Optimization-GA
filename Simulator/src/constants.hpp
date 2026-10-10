#pragma once

//#include <string>
#include <unordered_map>
#include <map>
#include <stdexcept>
#include <algorithm>

enum class GameFeatureType {
    BASEGAME,
    FREEGAME
};

enum class GameSymbols {
    AA,
    BB,
    CC,
    DD,
    EE,
    FF,
    GG,
    WD,
    SC,
    Invalid
};


const inline double Paytable[][3] = {
    // 3OK  4OK  5OK
    {  20,  100, 200 },  // AA = 0
    {  20,  100, 200 },  // BB = 1
    {  20,  100, 200 },  // CC = 2
    {  5,  20,  100 },  // DD = 3
    {  5,  20,  100 },  // EE = 4
    {  1,  10,  50 },  // FF = 5
    {  1,  10,  50 },  // GG = 6
    {  40,  400,  1000 },  // WD = 7
    {  10,   50,  500 },  // SC = 8
};

const inline std::vector<std::vector<int>> Paylines = {
    {1, 1, 1, 1, 1},  // 1
    {0, 0, 0, 0, 0},  // 2
    {2, 2, 2, 2, 2},  // 3
    {0, 1, 2, 1, 0},  // 4
    {2, 1, 0, 1, 2},  // 5
    {0, 0, 1, 0, 0},  // 6
    {2, 2, 1, 2, 2},  // 7
    {1, 2, 2, 2, 1},  // 8
    {1, 0, 0, 0, 1},  // 9
    {1, 0, 1, 0, 1},  // 10
    {1, 2, 1, 2, 1},  // 11
    {0, 1, 0, 1, 0},  // 12
    {2, 1, 2, 1, 2},  // 13
    {1, 1, 0, 1, 1},  // 14
    {1, 1, 2, 1, 1},  // 15
    {0, 1, 1, 1, 0},  // 16
    {2, 1, 1, 1, 2},  // 17
    {0, 1, 2, 2, 2},  // 18
    {2, 1, 0, 0, 0},  // 19
    {0, 2, 0, 2, 0},  // 20
};


struct GameFeatureConsts {
    GameFeatureType GAMEFEATURETYPE = GameFeatureType::BASEGAME;

    GameFeatureConsts(GameFeatureType type, GameFeatureType withoutScatterReelType)
        : GAMEFEATURETYPE(type){}
    GameFeatureConsts() = default;
};



namespace Constants {


    // ─────────────────────────────────────────────
    // File paths and sheet names
    // ─────────────────────────────────────────────
    inline const std::string reelSetFilePath = std::string(SOURCE_DIR) + "/src/reelset.json";
    inline const char* baseReelWorkBook = "BaseGameReel";
    inline const char* freeReelWorkBook = "FreeGameReel";
    inline const char* buyReelWorkBook = "Buy free spins";
    inline const int baseBet = 20;
    inline const int freeSpinsCount = 10;
    inline const int maxWin = 22000;
    // ─────────────────────────────────────────────
    // Matrix dimensions  [rows, cols]
    // ─────────────────────────────────────────────
    inline constexpr int matrixSize[2] = { 3,5 };

    inline GameSymbols gameSymbolFromString(const char* input) {

        std::string value(input);  // convert once at the top
        std::transform(value.begin(), value.end(), value.begin(), ::toupper);

        if (value == "AA") return GameSymbols::AA;
        if (value == "BB") return GameSymbols::BB;
        if (value == "CC") return GameSymbols::CC;
        if (value == "DD") return GameSymbols::DD;
        if (value == "EE") return GameSymbols::EE;
        if (value == "FF") return GameSymbols::FF;
        if (value == "GG") return GameSymbols::GG;
        if (value == "SC") return GameSymbols::SC;
        if (value == "WD") return GameSymbols::WD;

        else return GameSymbols::Invalid;
    }

    inline const char* stringFromGameSymbols(const GameSymbols value) {
        switch (value) {
        case GameSymbols::AA: return "AA";
        case GameSymbols::BB: return "BB";
        case GameSymbols::CC: return "CC";
        case GameSymbols::DD: return "DD";
        case GameSymbols::EE: return "EE";
        case GameSymbols::FF: return "FF";
        case GameSymbols::GG: return "GG";
        case GameSymbols::SC: return "SC";
        case GameSymbols::WD: return "WD";
        default:
            throw std::invalid_argument("Unknown GameSymbols value");
            //Print(value);

        }
    }

    inline bool runBaseOnly;

}

