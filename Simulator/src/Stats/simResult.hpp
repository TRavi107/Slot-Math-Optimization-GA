#pragma once
#include "baseMatrixData.hpp"
#include "freeMatrixData.hpp"
#include "buyFreematrixData.hpp"
#include <iostream>
// ─────────────────────────────────────────────
// SimResult
// ─────────────────────────────────────────────
struct SimResult {
    long long spinCount = 0;
    int BASEBET = 0;
    int maxWin = 0;

    BaseMatrixData  base;
    FreeMatrixData  free;
    BuyFreeMatrixData buyGame;

    double totalRTP = 0.f;
    double overallHitRate = 0.f;

    double currentSpinWin = 0.f;
    double totalWins = 0.f;
    double maxWinCount = 0;
    double achievedMaxWin = 0.f;

    std::unordered_map<std::string, double> winDistribution;

    SimResult() = default;
    SimResult(long long _spinCount,int baseBet, int maxWin_) {
        BASEBET = baseBet;
        maxWin = maxWin_;
        spinCount = _spinCount;
        base = BaseMatrixData(spinCount, baseBet);
        free = FreeMatrixData(spinCount, baseBet);
        buyGame = BuyFreeMatrixData(spinCount, baseBet);
    }

    SimResult& operator+=(const SimResult& other) {
        base += other.base;
        free += other.free;
        buyGame += other.buyGame;
        totalWins += other.totalWins;
        maxWinCount += other.maxWinCount;
        achievedMaxWin = std::max(achievedMaxWin, other.achievedMaxWin);

        for (const auto& [key, val] : other.winDistribution)
            winDistribution[key] += val;

        return *this;
    }

    // operator+ then becomes trivial and benefits from NRVO
    SimResult operator+(const SimResult& other) const {
        SimResult result = *this;   // copy once
        result += other;            // modify in place
        return result;              // NRVO eliminates this copy
    }

    void calculate() {
        base.calculate();
        free.calculate();
        buyGame.calculate();
        totalRTP = base.rtp+free.rtp;

        long long totalTriggers = 0;
        overallHitRate = (spinCount*1.0) / (totalTriggers != 0 ? totalTriggers : 1);
    }

    bool CheckIfMaxWinReached(double amount) const {
        return (maxWin - (currentSpinWin + amount)) <= 0.f;
    }

    void UpdateSpinWinnings(double amount) {
        currentSpinWin += amount;
        if (currentSpinWin >= maxWin) {
            currentSpinWin = maxWin;
            maxWinCount++;
        }
    }

    double GetRemainingFromMaxWin() const {
        
        return maxWin - currentSpinWin;
    }

    void ResetSpinWinnings() {
        totalWins += currentSpinWin;
        currentSpinWin = 0.f;
    }

    void AddSpinWinnings() {
        double total = base.thisSpinWinnings+free.thisSpinWinnings+buyGame.thisSpinWinnings;

        // if (currentSpinWin != total)
        //     std::cout << "current spin win " << total << " " << currentSpinWin << "\n";

        _updateWinDistribution(total);

        if (total > achievedMaxWin) achievedMaxWin = total;

        base.ResetSpinWinnings();
        free.ResetSpinWinnings();
        buyGame.ResetSpinWinnings();
    }

private:
    void _updateWinDistribution(double winAmount) {
        double m = winAmount / BASEBET;
        if(m==0) winDistribution["0"] += 1;
        else if (m < 1)  winDistribution["0-1"] += 1;
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
        else if (m < 800) winDistribution["700-800"] += 1;
        else             winDistribution["800+"] += 1;
    }
};