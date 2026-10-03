
#include <iostream>
#include <vector>
#include "constants.hpp"
#include "reelsFunction.hpp"
#include "Utility/Utilities.hpp"
#include "Stats/simResult.hpp"
#include "WinningFunctions.hpp"
#include "multiThread/SimRunner.hpp"

std::vector<std::vector<GameSymbols>> baseReels;
std::vector<std::vector<GameSymbols>> freeReels;
std::vector<std::vector<GameSymbols>> buyReelsStrip;
std::vector<std::vector<GameSymbols>> buyFreeReels;

void PopulateReelsData(const std::string excelFilePath, int cols) {
    ReelFunctions::get_reel_data(Constants::baseReelWorkBook, excelFilePath.c_str(), baseReels, cols,0);
    ReelFunctions::get_reel_data(Constants::freeReelWorkBook, excelFilePath.c_str(), freeReels, cols, 0);
    // ReelFunctions::get_reel_data(Constants::buyReelWorkBook, excelFilePath.c_str(), buyReelsStrip, cols, 0);
    // ReelFunctions::get_reel_data(Constants::buyReelWorkBook, excelFilePath.c_str(), buyFreeReels, cols, 6);

    //for (const auto reel : buyFreeReels) {
    //    for (const auto sym : reel) {
    //        std::cout << Constants::stringFromGameSymbols(sym)<<" ";
    //    }
    //    std::cout << "\n";
    //}
}

void free_game(SimResult& result)
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
    while (freeSpinCount > 0) {
        winnings = 0;
        scatterCount = 0;

        ReelFunctions::generate_slot_matrix(freeReels, Constants::matrixSize, matrix);

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

void RunSim(long spinCount, SimResult& result) {

    double totalWin = 0;

    //const int matrixSize[2] = { 3,3 };
    std::vector<std::vector<GameSymbols>> matrix(
        Constants::matrixSize[0], std::vector<GameSymbols>(Constants::matrixSize[1])
    );
    int scatterCount = 0;
    double winnings = 0;
    double win = 0;
    for (int i = 0; i < spinCount; i++)
    {
        //buy_free_game(spinCount, result);

        ReelFunctions::generate_slot_matrix(baseReels, Constants::matrixSize, matrix);

        //generate_slot_matrix(GameFeatureType::REDFREEGAME, matrixSize, matrix);
        //check winnings 
        //matrix = {
        //    {GameSymbols::SC,GameSymbols::BB,GameSymbols::CC,GameSymbols::DD,GameSymbols::EE},
        //    {GameSymbols::WD,GameSymbols::WD,GameSymbols::WD,GameSymbols::WD,GameSymbols::GG},
        //    {GameSymbols::CC,GameSymbols::SC,GameSymbols::EE,GameSymbols::FF,GameSymbols::AA},
        //};
        scatterCount = 0;

        winnings = WinningFunctions::check_paylines(matrix, result.base, 1 );

        WinningFunctions::ScattersCount(matrix, scatterCount, GameSymbols::SC);
        
        if (result.CheckIfMaxWinReached(winnings)) {
            winnings = result.GetRemainingFromMaxWin();
            result.base.updateWinnings(winnings);
            result.UpdateSpinWinnings(winnings);

            result.AddSpinWinnings();
            result.ResetSpinWinnings();
            break;
        }

        if (scatterCount >= 3 && scatterCount <=5) {
            win = Paytable[static_cast<int>(GameSymbols::SC)][scatterCount - 3]*Constants::baseBet;
            winnings += win;
            // if (scatterCount != 3 && scatterCount != 4 && scatterCount != 5)
            //     std::cout << "Scatter is more " << scatterCount << std::endl;
            result.base.updateSymbolsData(win,scatterCount,GameSymbols::SC);
            if (result.CheckIfMaxWinReached(winnings)) {
                winnings = result.GetRemainingFromMaxWin();
                result.base.updateWinnings(winnings);
                result.UpdateSpinWinnings(winnings);

                result.AddSpinWinnings();
                result.ResetSpinWinnings();
                break;
            }

            free_game(result);
        }

        result.base.updateWinnings(winnings);
        result.UpdateSpinWinnings(winnings);

        result.AddSpinWinnings();
        result.ResetSpinWinnings();
        //print winnings
        //totalWin += winnings;
    }
    //return result;
    //std::cout << "Total wins " << static_cast<long long>( totalWin) << "\n";
}
SimResult SimRunnerInit(const long spinCount) {
    return SimResult(spinCount,Constants::baseBet, Constants::maxWin);
 }

 static void writeResultsJson(const std::string& path, const SimResult& r, long spinCount)
    {
        std::ostringstream j;
        j << std::setprecision(17);
        j << "{\n"
        << "  \"spinCount\": "      << spinCount << ",\n"
        << "  \"baseHitRate\": "    << r.base.hitRate << ",\n"
        << "  \"baseRTP\": "        << r.base.rtp << ",\n"
        << "  \"freeHitRate\": "    << r.free.hitRate << ",\n"
        << "  \"freeRTP\": "        << r.free.rtp << ",\n"
        << "  \"freeAvgSpins\": "   << r.free.averageSpins << ",\n"
        << "  \"freeTriggerRate\": "<< r.free.triggerRate << ",\n"
        << "  \"totalRTP\": "       << r.totalRTP << ",\n"
        << "  \"totalWins\": "      << static_cast<long long>(r.totalWins) << ",\n"
        << "  \"maxWinCount\": "    << r.maxWinCount << ",\n"
        << "  \"winDistribution\": {";

        bool first = true;
        for (const auto& [bucket, value] : r.winDistribution) {
            j << (first ? "\n    " : ",\n    ")
            << "\"" << MiniJson::jsonEscape(bucket) << "\": " << value;
            first = false;
        }
        j << "\n  }\n}\n";

        std::ofstream out(path, std::ios::binary);
        if (!out) throw std::runtime_error("failed to write results file '" + path + "'");
        out << j.str();
    }

int main(int argc, char* argv[])
{
    try{
        std::string reelSetPath = (argc > 2) ? std::string(argv[2]) : Constants::reelSetFilePath;

        PopulateReelsData(reelSetPath,Constants::matrixSize[1]);

        long spinCount = 0;

        if (argc > 1) {
            // from command line: myapp.exe 10000000
            char* end = nullptr;
            errno = 0;
            spinCount = std::strtol(argv[1], &end, 10);
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

        SimResult result = SimResult(spinCount, Constants::baseBet, Constants::maxWin);

        // RunSim(spinCount, result);
        result = SimRunner::RunMultiThreadSim<SimResult>(spinCount, SimRunnerInit, RunSim);
        result.calculate();

        if (argc > 3)
            writeResultsJson(argv[3], result, spinCount);

        std::vector<std::pair<GameSymbols, /*ValueType*/ decltype(result.base.symbolsData)::mapped_type>>
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

        std::vector<std::pair<GameSymbols, /*ValueType*/ decltype(result.free.symbolsData)::mapped_type>>
            frows(result.free.symbolsData.begin(), result.free.symbolsData.end());

        std::sort(frows.begin(), frows.end(),
            [](const auto& a, const auto& b) { return a.first < b.first; });

        //for (const auto& [symbol, data] : frows) {
        //    std::cout << std::left << std::setw(10) << Constants::stringFromGameSymbols(symbol)
        //        << std::setw(12) << data.rtp * 100 << std::setw(12) << data.hitrate << std::setw(12) << data.hitrate3OK << std::setw(12) << data.hitrate4OK << std::setw(12) << data.hitrate5OK << "\n";
        //}
        std::cout << "free Hitrate " << result.free.hitRate << '\n';
        std::cout << "Free RTP: " << result.free.rtp * 100 << '\n';
        std::cout << "Free average free spins " << result.free.averageSpins << '\n';
        std::cout << "Free average wins " << result.free.averageWinsPerTrigger << '\n';
        std::cout << "Free Trigger rate: " << result.free.triggerRate << '\n';
        std::cout << "Free RETrigger rate: " << result.free.retriggerRate<< '\n';

        std::cout << "==============Overall Game=============== " << '\n';
        // Copy out so we can order it (unordered_map has no order)
        std::vector<std::pair<std::string, double>> drows(
            result.winDistribution.begin(), result.winDistribution.end());

        // sort by key (bucket name) ascending
        std::sort(drows.begin(), drows.end(),
            [](const auto& a, const auto& b) { return a.second > b.second; });

        // header
        std::cout << std::left << std::setw(18) << "Bucket"
            << std::right << std::setw(14) << "Value" << "\n";
        std::cout << std::string(32, '-') << "\n";

        std::cout << std::fixed << std::setprecision(4);
        for (const auto& [bucket, value] : drows) {
            std::cout << std::left << std::setw(18) << bucket
                << std::right << std::setw(14) << value << std::setw(14) << value/spinCount*100 << "\n";
        }
        //std::cout << "Buy strip wins " << result.buyGame. << '\n';

        std::cout << "RTP: " << result.totalRTP * 100 << '\n';
        std::cout << "Total wins " << static_cast<long long>( result.totalWins)<< '\n';
        std::cout << "Achieved Max win " << result.achievedMaxWin << '\n';
        std::cout << "Max Win Count " << result.maxWinCount << '\n';     
    }
    catch (const std::exception& e) {
        printf("ERROR: %s\n", e.what());
        return 1;
    }    
    // WaitForKey waitForKey;
    return 0;
}

