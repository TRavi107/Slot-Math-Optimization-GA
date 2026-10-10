#pragma once
#include <vector>
#include <array>
#include "constants.hpp"
#include "Stats/reelMatrixData.hpp"
#include "Stats/freeMatrixData.hpp"

namespace WinningFunctions {

    using Matrix = std::vector<std::vector<GameSymbols>>; 

    inline void ScattersCount(const Matrix& matrix, int& scatterCount, GameSymbols scatterSymbol) {
        for (const auto& row : matrix) {
            for (int col = 0; col < row.size(); col++)
                if (row[col] == scatterSymbol) 
                    scatterCount++; 
            //break;
        }
    }

    inline double check_paylines(const Matrix& matrix, ReelMatrixData& reelMatrix, const int multiplier = 1)
    {
        double totalWin = 0.0;
        const int linesLength = static_cast<int>(Paylines[0].size());

        for (const std::vector<int>& payline : Paylines) {
            const GameSymbols first = matrix[payline[0]][0];
            if (first == GameSymbols::SC)
                continue;

            if (first == GameSymbols::WD) {
                // Count leading wilds
                int wildCount = 1;
                while (wildCount < linesLength &&
                    matrix[payline[wildCount]][wildCount] == GameSymbols::WD)
                    ++wildCount;

                const double wildPay = (wildCount >= 3)
                    ? Paytable[static_cast<int>(GameSymbols::WD)][wildCount - 3]
                    : 0.0;

                // Candidate: wilds extend the first non-wild symbol
                double symPay = 0.0;
                GameSymbols sym = GameSymbols::WD;
                int symCount = 0;
                if (wildCount < linesLength) {
                    sym = matrix[payline[wildCount]][wildCount];
                    if (sym != GameSymbols::SC) {
                        symCount = wildCount + 1;
                        for (int col = wildCount + 1; col < linesLength; ++col) {
                            const GameSymbols s = matrix[payline[col]][col];
                            if (s == sym || s == GameSymbols::WD) ++symCount;
                            else break;
                        }
                        if (symCount >= 3)
                            symPay = Paytable[static_cast<int>(sym)][symCount - 3];
                    }
                }

                const bool useSym = symPay > wildPay;
                const double payout = useSym ? symPay : wildPay;
                if (payout > 0) {
                    totalWin += payout;
                    reelMatrix.updateSymbolsData(payout * multiplier,
                        useSym ? symCount : wildCount,
                        useSym ? sym : GameSymbols::WD);
                }
            }
            else {
                int matchCount = 1;
                for (int col = 1; col < linesLength; ++col) {
                    const GameSymbols s = matrix[payline[col]][col];
                    if (s == first || s == GameSymbols::WD) ++matchCount;
                    else break;
                }
                if (matchCount >= 3) {
                    const double payout = Paytable[static_cast<int>(first)][matchCount - 3];
                    if (payout > 0) {
                        totalWin += payout;
                        reelMatrix.updateSymbolsData(payout * multiplier, matchCount, first);
                    }
                }
            }
        }
        return totalWin * multiplier;
    }
}