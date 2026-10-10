#pragma once
#include "reelMatrixData.hpp"
// ─────────────────────────────────────────────
// FreeMatrixData
// ─────────────────────────────────────────────
struct FreeMatrixData : public ReelMatrixData {
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

    FreeMatrixData() = default;
    FreeMatrixData(long long spinCount, long long baseBet) : ReelMatrixData(spinCount, baseBet) {}

    FreeMatrixData& operator+=(const FreeMatrixData& other) {
        // base fields — addBase merges totalWins, winningSpins, symbolsData, winDistribution
        addBase(other);

        // derived fields
        totalFreeSpinsCount += other.totalFreeSpinsCount;
        triggerCount += other.triggerCount;
        retriggerCount += other.retriggerCount;
        maxFreeSpins = std::max(maxFreeSpins, other.maxFreeSpins);
        maxRetirgger = std::max(maxRetirgger, other.maxRetirgger);
        return *this;
    }

    void calculate() override {
        ReelMatrixData::calculate();
        triggerRate = SPINCOUNT / (triggerCount ? triggerCount : 1.f);
        averageSpins = totalFreeSpinsCount / (triggerCount ? triggerCount : 1.f);
        hitRate = totalFreeSpinsCount / (winningSpins ? winningSpins : 1.f);
        averageMultiplier = totalMultiplier / (totalFreeSpinsCount ? totalFreeSpinsCount : 1.f);
        retriggerRate = totalFreeSpinsCount / (retriggerCount ? retriggerCount : 1.f);
        averageWinsPerTrigger = totalWins /
            (triggerCount ? static_cast<double>(triggerCount) * BASEBET : 1.f);
    }

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