#pragma once
#include "reelMatrixData.hpp"
// ─────────────────────────────────────────────
// BaseMatrixData
// ─────────────────────────────────────────────
struct BuyFreeMatrixData : public ReelMatrixData {

    long long totalFreeSpinsCount = 0;
    long long triggerCount = 0;
    double triggerRate = 0.f;
    double averageSpins = 0.f;


    long long retriggerCount = 0;
    int maxRetirgger = 0;
    int thisSpinRetirgger = 0;
    double retriggerRate = 0.f;

    double averageWinsPerTrigger = 0.f;

    int thisSpinFreeSpins = 0;
    int maxFreeSpins = 0;

    double buyStripsWins = 0;
    double averagebuyStripsWins = 0;
    long scatterCount[3] = {0,0,0};

    BuyFreeMatrixData() = default;
    BuyFreeMatrixData(long long spinCount, long long baseBet) : ReelMatrixData(spinCount, baseBet) {}

    BuyFreeMatrixData& operator+=(const BuyFreeMatrixData& other) {
        // base fields — addBase merges totalWins, winningSpins, symbolsData, winDistribution
        addBase(other);

        // derived fields
        totalFreeSpinsCount += other.totalFreeSpinsCount;
        triggerCount += other.triggerCount;
        retriggerCount += other.retriggerCount;
        maxFreeSpins = std::max(maxFreeSpins, other.maxFreeSpins);
        maxRetirgger = std::max(maxRetirgger, other.maxRetirgger);
        buyStripsWins += other.buyStripsWins;
        for (int i = 0; i < 3; i++)
        {
            scatterCount[i] += other.scatterCount[i];
        }
        return *this;
    }
    //void AddBuyStripWins(const int& _scatterCount,const double& winAmount) {
    //    totalWins += winAmount;
    //    buyStripsWins += winAmount;
    //    scatterCount[_scatterCount - 3] += 1;
    //}
    void calculate() override {
        ReelMatrixData::calculate();
        triggerRate = SPINCOUNT / (triggerCount ? triggerCount : 1.f);
        averageSpins = totalFreeSpinsCount / (triggerCount ? triggerCount : 1.f);
        hitRate = totalFreeSpinsCount / (winningSpins ? winningSpins : 1.f);
        averageMultiplier = totalMultiplier / (totalFreeSpinsCount ? totalFreeSpinsCount : 1.f);
        retriggerRate = totalFreeSpinsCount / (retriggerCount ? retriggerCount : 1.f);
        averageWinsPerTrigger = totalWins /
            (triggerCount ? static_cast<double>(triggerCount) * BASEBET : 1.f);

        averagebuyStripsWins = buyStripsWins / triggerCount;
        
    }
    //void updateWinnings(double currentWin) override {
    //    ReelMatrixData::updateWinnings(currentWin);
    //    buyStripsWins += currentWin;
    //}
    
    void AddFreeSpins(const int spins, const bool isRetrigger = false) {
        totalFreeSpinsCount += spins;
        thisSpinFreeSpins += spins;
        if (isRetrigger) {
            retriggerCount++;
            thisSpinRetirgger++;
        }
    }
    void ResetFreeSpin() {
        if (thisSpinFreeSpins > maxFreeSpins) {
            maxFreeSpins = thisSpinFreeSpins;
            //std::cout << thisSpinWinnings<<"\n";
        }
        if (thisSpinRetirgger > maxRetirgger)
            maxRetirgger = thisSpinRetirgger;
        thisSpinFreeSpins = 0;
        thisSpinRetirgger = 0;
    }
    void AddFreeTriggerCount(double /*spins*/) { triggerCount++; }
};