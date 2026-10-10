#include <algorithm>
#include <cerrno>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <vector>
#include "constants.hpp"
#include "reelsFunction.hpp"
#include "Utility/Utilities.hpp"
#include "Utility/rng.hpp"
#include "Stats/simResult.hpp"
#include "WinningFunctions.hpp"
#include "multiThread/SimRunner.hpp"

// Usage:
//   simulator <spins> [reelset.json] [runBaseOnly true|false] [out.json] [seed]
//
// Same <spins>, reelset, runBaseOnly and <seed>  ->  bit-identical results,
// on any machine and any number of CPU cores.
// Without a seed a random one is chosen and printed, so the run can be replayed.

std::vector<std::vector<GameSymbols>> baseReels;
std::vector<std::vector<GameSymbols>> freeReels;
std::vector<std::vector<GameSymbols>> buyReelsStrip;
std::vector<std::vector<GameSymbols>> buyFreeReels;

void PopulateReelsData(const std::string excelFilePath, int cols) {
    ReelFunctions::get_reel_data(Constants::baseReelWorkBook, excelFilePath.c_str(), baseReels, cols,0);
    ReelFunctions::get_reel_data(Constants::freeReelWorkBook, excelFilePath.c_str(), freeReels, cols, 0);
    // ReelFunctions::get_reel_data(Constants::buyReelWorkBook, excelFilePath.c_str(), buyReelsStrip, cols, 0);
    // ReelFunctions::get_reel_data(Constants::buyReelWorkBook, excelFilePath.c_str(), buyFreeReels, cols, 6);
}

void free_game(SimResult& result, Rng::Xoshiro256ss& rng)
{
    int freeSpinCount = Constants::freeSpinsCount;
    result.free.AddFreeTriggerCount(1);
    result.free.AddFreeSpins(freeSpinCount);

    std::vector<std::vector<GameSymbols>> matrix(
        Constants::matrixSize[0], std::vector<GameSymbols>(Constants::matrixSize[1])
    );

    double winnings = 0;
    int scatterCount =0;
    double win = 0;
    if(Constants::runBaseOnly )
        return; //to skip free game but count trigger rate
    while (freeSpinCount > 0) {
        winnings = 0;
        scatterCount = 0;

        ReelFunctions::generate_slot_matrix(freeReels, Constants::matrixSize, matrix, rng);

        winnings = WinningFunctions::check_paylines(matrix, result.free, 1 );
        WinningFunctions::ScattersCount(matrix, scatterCount, GameSymbols::SC);
        if (result.CheckIfMaxWinReached(winnings)) {
            winnings = result.GetRemainingFromMaxWin();
            result.free.updateWinnings(winnings);
            result.UpdateSpinWinnings(winnings);
            break;
        }

        if (scatterCount>=3) {
            win = Paytable[static_cast<int>(GameSymbols::SC)][scatterCount - 3] * Constants::baseBet;
            winnings += win;
            result.free.updateSymbolsData(win, scatterCount, GameSymbols::SC);
            if (result.CheckIfMaxWinReached(winnings)) {
                winnings = result.GetRemainingFromMaxWin();
                result.free.updateWinnings(winnings);
                result.UpdateSpinWinnings(winnings);
                break;
            }

            freeSpinCount += Constants::freeSpinsCount;
            result.free.AddFreeSpins(Constants::freeSpinsCount, true);
        }
        result.free.updateWinnings(winnings);
        result.free.thisSpinFreeSpins++;
        --freeSpinCount;

        result.UpdateSpinWinnings(winnings);
    }

    result.free.ResetFreeSpin();
}

void RunSim(long long spinCount, SimResult& result, Rng::Xoshiro256ss& rng) {

    std::vector<std::vector<GameSymbols>> matrix(
        Constants::matrixSize[0], std::vector<GameSymbols>(Constants::matrixSize[1])
    );
    int scatterCount = 0;
    double winnings = 0;
    double win = 0;
    for (long long i = 0; i < spinCount; i++)
    {
        ReelFunctions::generate_slot_matrix(baseReels, Constants::matrixSize, matrix, rng);

        scatterCount = 0;

        winnings = WinningFunctions::check_paylines(matrix, result.base, 1 );

        WinningFunctions::ScattersCount(matrix, scatterCount, GameSymbols::SC);

        if (result.CheckIfMaxWinReached(winnings)) {
            winnings = result.GetRemainingFromMaxWin();
            result.base.updateWinnings(winnings);
            result.UpdateSpinWinnings(winnings);

            result.AddSpinWinnings();
            result.ResetSpinWinnings();
            break;   // NOTE: existing behaviour — skips the rest of this job's spins
        }

        if (scatterCount >= 3 && scatterCount <=5) {
            win = Paytable[static_cast<int>(GameSymbols::SC)][scatterCount - 3]*Constants::baseBet;
            winnings += win;
            result.base.updateSymbolsData(win,scatterCount,GameSymbols::SC);
            if (result.CheckIfMaxWinReached(winnings)) {
                winnings = result.GetRemainingFromMaxWin();
                result.base.updateWinnings(winnings);
                result.UpdateSpinWinnings(winnings);

                result.AddSpinWinnings();
                result.ResetSpinWinnings();
                break;   // NOTE: existing behaviour — skips the rest of this job's spins
            }

            free_game(result, rng);
        }

        result.base.updateWinnings(winnings);
        result.UpdateSpinWinnings(winnings);

        result.AddSpinWinnings();
        result.ResetSpinWinnings();
    }
}

SimResult SimRunnerInit(const long long spinCount) {
    return SimResult(spinCount, Constants::baseBet, Constants::maxWin);
}

static void writeResultsJson(const std::string& path, const SimResult& r,
                             long long spinCount, uint64_t seed)
{
    std::ostringstream j;
    j << std::setprecision(17);
    j << "{\n"
    // seed as a string: 64-bit integers lose precision in many JSON readers
    << "  \"seed\": \""          << seed << "\",\n"
    << "  \"spinCount\": "      << spinCount << ",\n"
    << "  \"baseHitRate\": "    << r.base.hitRate << ",\n"
    << "  \"baseRTP\": "        << r.base.rtp << ",\n"
    << "  \"freeHitRate\": "    << r.free.hitRate << ",\n"
    << "  \"freeRTP\": "        << r.free.rtp << ",\n"
    << "  \"freeAvgSpins\": "   << r.free.averageSpins << ",\n"
    << "  \"freeTriggerRate\": "<< r.free.triggerRate << ",\n"
    << "  \"freeReTriggerRate\": "<< r.free.retriggerRate << ",\n"
    << "  \"totalRTP\": "       << r.totalRTP << ",\n"
    << "  \"totalWins\": "      << static_cast<long long>(r.totalWins) << ",\n"
    << "  \"maxWinCount\": "    << r.maxWinCount << ",\n"
    << "  \"winDistribution\": {";

    // sorted keys -> byte-identical file for identical results
    std::vector<std::pair<std::string, double>> buckets(r.winDistribution.begin(), r.winDistribution.end());
    std::sort(buckets.begin(), buckets.end(),
        [](const auto& a, const auto& b) { return a.first < b.first; });

    bool first = true;
    for (const auto& [bucket, value] : buckets) {
        j << (first ? "\n    " : ",\n    ")
        << "\"" << MiniJson::jsonEscape(bucket) << "\": " << value;
        first = false;
    }
    j << "\n  }\n}\n";

    std::ofstream out(path, std::ios::binary);
    if (!out) throw std::runtime_error("failed to write results file '" + path + "'");
    out << j.str();
}

static uint64_t parseSeed(const char* text) {
    char* end = nullptr;
    errno = 0;
    unsigned long long v = std::strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' || text[0] == '-')
        throw std::runtime_error(std::string("invalid seed '") + text + "' (use a non-negative integer)");
    return static_cast<uint64_t>(v);
}

int main(int argc, char* argv[])
{
    try{
        std::string reelSetPath = (argc > 2) ? std::string(argv[2]) : Constants::reelSetFilePath;

        PopulateReelsData(reelSetPath,Constants::matrixSize[1]);

        long long spinCount = 0;

        if (argc > 1) {
            // from command line: myapp.exe 10000000
            char* end = nullptr;
            errno = 0;
            spinCount = std::strtoll(argv[1], &end, 10);
            if (errno != 0 || end == argv[1] || *end != '\0' || spinCount <= 0) {
                printf("ERROR: invalid spin count '%s'\n", argv[1]);
                return 1;
            }
        }
        else {
            // prompt
            std::cout << "Enter spin count: ";
            if (!(std::cin >> spinCount) || spinCount <= 0) {
                printf("ERROR: invalid spin count\n");
                return 1;
            }
        }

        if (argc > 3) {
            std::string arg = argv[3];
            std::transform(arg.begin(), arg.end(), arg.begin(),
                [](unsigned char c) { return static_cast<char>(std::tolower(c)); });

            if (arg == "1" || arg == "true" || arg == "yes")
                Constants::runBaseOnly = true;
            else if (arg == "0" || arg == "false" || arg == "no")
                Constants::runBaseOnly  = false;
            else {
                printf("ERROR: invalid runOnlyBase '%s' (use true/false or 1/0)\n", argv[3]);
                return 1;
            }
        }

        // ---- seed (argv[5]) ----
        uint64_t seed;
        if (argc > 5) {
            seed = parseSeed(argv[5]);
        } else {
            std::random_device rd;
            seed = (static_cast<uint64_t>(rd()) << 32) | rd();
        }
        std::cout << "Seed: " << seed << '\n';

        SimResult result = SimRunner::RunMultiThreadSim<SimResult>(spinCount, seed, SimRunnerInit, RunSim);
        result.calculate();

        if (argc > 4)                                   // argv[4] exists only when argc > 4
            writeResultsJson(argv[4], result, spinCount, seed);

        std::vector<std::pair<GameSymbols, decltype(result.base.symbolsData)::mapped_type>>
            rows(result.base.symbolsData.begin(), result.base.symbolsData.end());

        std::sort(rows.begin(), rows.end(),
            [](const auto& a, const auto& b) { return a.first < b.first; });

        for (const auto& [symbol, data] : rows) {
            std::cout << std::left << std::setw(10) << Constants::stringFromGameSymbols(symbol)
                << std::setw(12) << data.totalWins << std::setw(12) << data.hitrate << std::setw(12) << data.hitrate3OK << std::setw(12) << data.hitrate4OK << std::setw(12) << data.hitrate5OK << "\n";
        }
        std::cout << "Base Hitrate " << result.base.hitRate << '\n';
        std::cout << "Base RTP: " << result.base.rtp * 100 << '\n';

        std::cout << "==============Free Game=============== "<< '\n';

        std::cout << "free Hitrate " << result.free.hitRate << '\n';
        std::cout << "Free RTP: " << result.free.rtp * 100 << '\n';
        std::cout << "Free average free spins " << result.free.averageSpins << '\n';
        std::cout << "Free average wins " << result.free.averageWinsPerTrigger << '\n';
        std::cout << "Free Trigger rate: " << result.free.triggerRate << '\n';
        std::cout << "Free RETrigger rate: " << result.free.retriggerRate<< '\n';

        std::cout << "==============Overall Game=============== " << '\n';
        std::vector<std::pair<std::string, double>> drows(
            result.winDistribution.begin(), result.winDistribution.end());

        std::sort(drows.begin(), drows.end(),
            [](const auto& a, const auto& b) { return a.second > b.second; });

        std::cout << std::left << std::setw(18) << "Bucket"
            << std::right << std::setw(14) << "Value" << "\n";
        std::cout << std::string(32, '-') << "\n";

        std::cout << std::fixed << std::setprecision(4);
        for (const auto& [bucket, value] : drows) {
            std::cout << std::left << std::setw(18) << bucket
                << std::right << std::setw(14) << value << std::setw(14) << value/spinCount*100 << "\n";
        }

        std::cout << "RTP: " << result.totalRTP * 100 << '\n';
        std::cout << "Total wins " << static_cast<long long>( result.totalWins)<< '\n';
        std::cout << "Achieved Max win " << result.achievedMaxWin << '\n';
        std::cout << "Max Win Count " << result.maxWinCount << '\n';
    }
    catch (const std::exception& e) {
        printf("ERROR: %s\n", e.what());
        return 1;
    }
    return 0;
}