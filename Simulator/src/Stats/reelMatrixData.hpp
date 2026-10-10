#pragma once
#include "symbolsData.hpp"

struct ReelMatrixData {
    long long SPINCOUNT = 0;
    int BASEBET = 0;

    long long winningSpins = 0;
    double totalWins = 0.f;
    double hitRate = 0.f;
    double rtp = 0.f;
    double thisSpinWinnings = 0.f;

    double averageMultiplier = 0.f;
    long long totalMultiplier = 0;

    std::unordered_map<GameSymbols, SymbolData>  symbolsData;
    std::unordered_map<std::string, double>   winDistribution;


    ReelMatrixData() = default;
    ReelMatrixData(long long spinCount, int baseBet)
        : SPINCOUNT(spinCount), BASEBET(baseBet) {
    }

    virtual ~ReelMatrixData() = default;

    // Shared addition logic used by derived classes
    void addBase(const ReelMatrixData& other) {
        totalWins += other.totalWins;
        winningSpins += other.winningSpins;
        totalMultiplier += other.totalMultiplier;
        // Merge symbolsData
        for (auto& [key, val] : other.symbolsData) {
            auto it = symbolsData.find(key);
            if (it == symbolsData.end())
                symbolsData[key] = val;
            else
                it->second = it->second + val;
        }

        // Merge winDistribution
        for (auto& [key, val] : other.winDistribution)
            winDistribution[key] += val;

    }

    virtual void calculate() {
        rtp = (BASEBET * SPINCOUNT > 0) ? totalWins / (BASEBET * SPINCOUNT * 1.0) : 0.f;
        hitRate = (winningSpins > 0) ? SPINCOUNT / (winningSpins*1.0) : 0.f;
        averageMultiplier = totalMultiplier / (SPINCOUNT * 1.0);
        for (auto& [_, sym] : symbolsData)
            sym.calculate();
    }
    void AddMultiplier(int multiplier) { totalMultiplier += multiplier; }

    void ResetSpinWinnings() { thisSpinWinnings = 0.f; }

    void updateSymbolsData(double currentWin, int winningComCount, const GameSymbols symbol) {
        if (currentWin == 0.f) return;

        // Find or create — returns reference to existing or newly inserted element
        auto it = symbolsData.find(symbol);
        if (it == symbolsData.end()) {
            // Not found — insert a new SymbolData initialized for this symbol
            SymbolData newData;
            newData.SYMBOL = symbol;
            newData.TOTALSPINS = SPINCOUNT;
            newData.BASEBET = BASEBET;
            it = symbolsData.emplace(symbol, newData).first;
        }

        SymbolData& sd = it->second;  // ← reference, not copy — edits persist

        sd.winSpinsCount++;
        sd.UpdateWinningComb(winningComCount);
        sd.totalWins += currentWin;
    }

    virtual void updateWinnings(double currentWin) {
        if (currentWin == 0) return;
        totalWins += currentWin;
        if (totalWins < 0)
            return;
        winningSpins++;
        thisSpinWinnings += currentWin;

        double m = currentWin / BASEBET;
        if (m < 1)  winDistribution["0-1"] += 1;
        else if (m < 2)  winDistribution["1-2"] += 1;
        else if (m < 3)  winDistribution["2-3"] += 1;
        else if (m < 5)  winDistribution["3-5"] += 1;
        else if (m < 10) winDistribution["5-10"] += 1;
        else if (m < 20) winDistribution["10-20"] += 1;
        else if (m < 50) winDistribution["20-50"] += 1;
        else if (m < 100) winDistribution["50-100"] += 1;
        else if (m < 200) winDistribution["100-200"] += 1;
        else if (m < 300) winDistribution["200-300"] += 1;
        else if (m < 500) winDistribution["300-500"] += 1;
        else if (m < 600) winDistribution["500-600"] += 1;
        else if (m < 700) winDistribution["600-700"] += 1;
        else             winDistribution["700-"] += 1;
    }

    SymbolData& getOrCreateSymbolsData(const GameSymbols& symbol) {
        auto [it, inserted] = symbolsData.emplace(
            symbol, SymbolData(symbol, SPINCOUNT, BASEBET));
        return it->second;
    }
};