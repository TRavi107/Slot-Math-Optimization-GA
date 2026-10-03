#pragma once
#include "../constants.hpp"

struct SymbolData {
    GameSymbols SYMBOL;
    long long TOTALSPINS = 0;
    int BASEBET = 0;

    double  winSpinsCount = 0;
    double  winning3OK = 0;
    double  winning4OK = 0;
    double  winning5OK = 0;
    double hitrate3OK = 0;
    double hitrate4OK = 0;
    double hitrate5OK = 0;
    double totalWins = 0;
    double hitrate = 0;
    double rtp = 0;

    SymbolData() = default;
    SymbolData(GameSymbols symbol, long long totalSpins, int baseBet)
        : SYMBOL(symbol), TOTALSPINS(totalSpins), BASEBET(baseBet) {
    }

    SymbolData operator+(const SymbolData& other) const {
        SymbolData result(SYMBOL, TOTALSPINS, BASEBET);
        result.winSpinsCount = winSpinsCount + other.winSpinsCount;
        result.totalWins = totalWins + other.totalWins;
        result.winning3OK = winning3OK + other.winning3OK;
        result.winning4OK = winning4OK + other.winning4OK;
        result.winning5OK = winning5OK + other.winning5OK;
        result.TOTALSPINS +=other.TOTALSPINS;
        return result;
    }

    void calculate() {
        hitrate = (winSpinsCount > 0) ? TOTALSPINS / winSpinsCount : 0.f;
        rtp = (TOTALSPINS * BASEBET > 0) ? totalWins / (TOTALSPINS * BASEBET*1.0) : 0.f;
        hitrate3OK = (winning3OK > 0) ? static_cast<double>(TOTALSPINS) / winning3OK : 0.f;
        hitrate4OK = (winning4OK > 0) ? static_cast<double>(TOTALSPINS) / winning4OK : 0.f;
        hitrate5OK = (winning5OK > 0) ? static_cast<double>(TOTALSPINS) / winning5OK : 0.f;
    }

    void UpdateWinningComb(int winningComCount) {
        switch (winningComCount) {
        case 3: winning3OK++; break;
        case 4: winning4OK++; break;
        case 5: winning5OK++; break;
        default: break;
        }
    }
};