#pragma once
#include "reelMatrixData.hpp"
// BaseMatrixData
struct BaseMatrixData : public ReelMatrixData {
    BaseMatrixData() = default;
    BaseMatrixData(long long spinCount, int baseBet) : ReelMatrixData(spinCount, baseBet) {}

    BaseMatrixData operator+(const BaseMatrixData& other) const {
        BaseMatrixData result(SPINCOUNT, BASEBET);
        result.totalWins = totalWins + other.totalWins;
        result.winningSpins = winningSpins + other.winningSpins;

        result.symbolsData = symbolsData;
        result.winDistribution = winDistribution;
        result.addBase(other);
        return result;
    }

    BaseMatrixData& operator+=(const BaseMatrixData& other) {
        addBase(other);   // merges totalWins, winningSpins, symbolsData, winDistribution
        return *this;
    }
};
