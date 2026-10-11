#include <algorithm>
#include <cerrno>
#include <chrono>
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
#include "Utility/Rng.hpp"
#include "Stats/simResult.hpp"
#include "WinningFunctions.hpp"
#include "multiThread/SimRunner.hpp"

// Usage:
//   simulator <spins> [reelset.json] [mode] [out.json] [seed] [triggerRate]
//
//   mode  false     full game: base spins, free games played when triggered (default)
//         true      base game only: free games are counted (trigger rate) but not played
//         sessions  free-sessions mode: <spins> is the number of free-game SESSIONS to
//                   play directly, with no base spins. Needs [triggerRate] = the base
//                   game's trigger rate as "1 in X" (e.g. 80). A session does not depend
//                   on the base spin that triggered it (free_game() only uses the free
//                   reels and the RNG; the max-win cap inside it already covers only the
//                   session's own wins), so its stats equal the full game's:
//                       freeRTP           = average session win (x bet) / X
//                       freeHitRate       = free spins / winning free spins   (as before)
//                       freeReTriggerRate = free spins / retriggers           (as before)
//                       freeTriggerRate   = X (the value passed in)
//                   Base stats are 0 and totalRTP is the free-game part only. Use it to
//                   tune free reels while the base reels are fixed; validate the result
//                   with a full-game run.
//
// Same <spins>, reelset, mode, <seed> (and triggerRate)  ->  bit-identical results,
// on any machine and any number of CPU cores.
// Without a seed a random one is chosen and printed, so the run can be replayed.
//
// The output JSON also carries "compute" (time taken, threads used) and "build"
// (compiler, build type). Those describe the machine, not the game, so they differ
// between machines and between calls; every other field is reproducible.
//
// Environment: SIM_THREADS=<n> fixes the number of worker threads (default: 80% of
// the logical CPUs). It changes only the speed, never the results.

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

// Free-sessions mode: play `sessionCount` free-game sessions, each exactly as a base
// spin with 3+ scatters would start one. Per session the win is recorded the way RunSim
// records a base spin (win distribution, max win), so per-session totals line up.
void RunFreeSessions(long long sessionCount, SimResult& result, Rng::Xoshiro256ss& rng) {
    for (long long i = 0; i < sessionCount; i++) {
        free_game(result, rng);
        result.AddSpinWinnings();
        result.ResetSpinWinnings();
    }
}

SimResult SimRunnerInit(const long long spinCount) {
    return SimResult(spinCount, Constants::baseBet, Constants::maxWin);
}

// ─────────────────────────────────────────────
// Build description, recorded with every result so timings can be compared
// ─────────────────────────────────────────────
static std::string compilerName() {
#if defined(__clang__)
    return std::string("Clang ") + __clang_version__;
#elif defined(__GNUC__)
    return "GCC " + std::to_string(__GNUC__) + "." + std::to_string(__GNUC_MINOR__) + "." +
           std::to_string(__GNUC_PATCHLEVEL__);
#elif defined(_MSC_VER)
    return "MSVC " + std::to_string(_MSC_FULL_VER);
#else
    return "unknown";
#endif
}

static std::string buildType() {
#ifdef SIM_BUILD_TYPE
    const std::string t = SIM_BUILD_TYPE;     // from CMake ($<CONFIG>)
    if (!t.empty()) return t;
#endif
#ifdef NDEBUG
    return "unknown (NDEBUG set)";
#else
    return "unknown (no NDEBUG: likely Debug)";
#endif
}

// true = compiled with optimisation. GCC/Clang define __OPTIMIZE__ for -O1 and up;
// MSVC has no such macro, so Release (NDEBUG, no _DEBUG) is taken as optimised there.
static const char* optimised() {
#if defined(__OPTIMIZE__)
    return "true";
#elif defined(_MSC_VER) && defined(NDEBUG) && !defined(_DEBUG)
    return "true";
#elif defined(__GNUC__) || defined(__clang__)
    return "false";
#else
    return "null";
#endif
}

static std::string targetName() {
#if defined(_WIN32)
    std::string os = "windows";
#elif defined(__APPLE__)
    std::string os = "macos";
#elif defined(__linux__)
    std::string os = "linux";
#else
    std::string os = "unknown";
#endif
#if defined(__x86_64__) || defined(_M_X64)
    return os + "-x86_64";
#elif defined(__aarch64__) || defined(_M_ARM64)
    return os + "-arm64";
#else
    return os;
#endif
}

static void writeResultsJson(const std::string& path, const SimResult& r,
                             long long spinCount, uint64_t seed,
                             const SimRunner::RunInfo& run, double wallSeconds,
                             const char* mode, double triggerRateUsed)
{
    std::ostringstream j;
    j << std::setprecision(17);
    j << "{\n"
    // seed as a string: 64-bit integers lose precision in many JSON readers
    << "  \"seed\": \""          << seed << "\",\n"
    // fullGame | baseOnly | freeSessions. In freeSessions, spinCount is the number of
    // sessions played and triggerRateUsed the X the free RTP was divided by.
    << "  \"mode\": \""          << mode << "\",\n";
    if (triggerRateUsed > 0)
        j << "  \"sessions\": "        << spinCount << ",\n"
          << "  \"triggerRateUsed\": " << triggerRateUsed << ",\n";
    j << "  \"spinCount\": "      << spinCount << ",\n"
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

    // sorted keys -> byte-identical stats for identical results
    std::vector<std::pair<std::string, double>> buckets(r.winDistribution.begin(), r.winDistribution.end());
    std::sort(buckets.begin(), buckets.end(),
        [](const auto& a, const auto& b) { return a.first < b.first; });

    bool first = true;
    for (const auto& [bucket, value] : buckets) {
        j << (first ? "\n    " : ",\n    ")
        << "\"" << MiniJson::jsonEscape(bucket) << "\": " << value;
        first = false;
    }
    j << "\n  },\n";

    // machine-dependent: how long this call took and how it was built
    j << std::setprecision(6)
      << "  \"compute\": {\n"
      << "    \"wallSeconds\": "     << wallSeconds << ",\n"       // whole program up to here
      << "    \"simSeconds\": "      << run.seconds << ",\n"       // spinning + merging only
      << "    \"threads\": "         << run.workers << ",\n"
      << "    \"hardwareThreads\": " << run.hardwareThreads << ",\n"
      << "    \"jobs\": "            << run.jobs << ",\n"
      << "    \"spinsPerSecond\": "  << (run.seconds > 0 ? spinCount / run.seconds : 0.0) << "\n"
      << "  },\n"
      << "  \"build\": {\n"
      << "    \"compiler\": \""  << MiniJson::jsonEscape(compilerName()) << "\",\n"
      << "    \"buildType\": \"" << MiniJson::jsonEscape(buildType()) << "\",\n"
      << "    \"optimized\": "   << optimised() << ",\n"
      << "    \"cxxStandard\": " << __cplusplus << ",\n"
      << "    \"target\": \""    << targetName() << "\"\n"
      << "  }\n}\n";

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

// SIM_THREADS environment variable, 0 = not set (use the default)
static int threadOverride() {
    const char* v = std::getenv("SIM_THREADS");
    if (!v || !*v) return 0;
    char* end = nullptr;
    long n = std::strtol(v, &end, 10);
    if (*end != '\0' || n <= 0)
        throw std::runtime_error(std::string("invalid SIM_THREADS '") + v + "' (use a positive integer)");
    return static_cast<int>(n);
}

int main(int argc, char* argv[])
{
    const auto programStart = std::chrono::steady_clock::now();
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

        bool sessionsMode = false;
        if (argc > 3) {
            std::string arg = argv[3];
            std::transform(arg.begin(), arg.end(), arg.begin(),
                [](unsigned char c) { return static_cast<char>(std::tolower(c)); });

            if (arg == "1" || arg == "true" || arg == "yes")
                Constants::runBaseOnly = true;
            else if (arg == "0" || arg == "false" || arg == "no")
                Constants::runBaseOnly  = false;
            else if (arg == "sessions") {
                Constants::runBaseOnly = false;
                sessionsMode = true;
            }
            else {
                printf("ERROR: invalid mode '%s' (use true/false, 1/0 or sessions)\n", argv[3]);
                return 1;
            }
        }

        // ---- trigger rate (argv[6]), sessions mode only ----
        double triggerRate = 0.0;
        if (sessionsMode) {
            if (argc <= 6) {
                printf("ERROR: sessions mode needs the trigger rate as argument 6 "
                       "(\"1 in X\", e.g. 80)\n");
                return 1;
            }
            char* end = nullptr;
            errno = 0;
            triggerRate = std::strtod(argv[6], &end);
            if (errno != 0 || end == argv[6] || *end != '\0' || !(triggerRate >= 1.0)) {
                printf("ERROR: invalid trigger rate '%s' (a number >= 1, \"1 in X\")\n", argv[6]);
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

        SimRunner::RunInfo runInfo;
        SimResult result = sessionsMode
            ? SimRunner::RunMultiThreadSim<SimResult>(spinCount, seed, SimRunnerInit, RunFreeSessions,
                                                      threadOverride(), &runInfo, SimRunner::JOB_SESSIONS)
            : SimRunner::RunMultiThreadSim<SimResult>(spinCount, seed, SimRunnerInit, RunSim,
                                                      threadOverride(), &runInfo);
        result.calculate();

        const char* mode = sessionsMode ? "freeSessions"
                         : (Constants::runBaseOnly ? "baseOnly" : "fullGame");
        if (sessionsMode) {
            // calculate() divided by the number of sessions, so free.rtp is now the
            // average session win in bets. Per base spin that is 1/X of it.
            result.free.rtp /= triggerRate;
            result.free.triggerRate = triggerRate;
            result.totalRTP = result.free.rtp;
            std::cout << "Mode: free sessions (" << spinCount << " sessions, trigger rate 1 in "
                      << triggerRate << ")\n";
        }

        const double wallSeconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - programStart).count();
        std::cout << "Time: " << runInfo.seconds << " s on " << runInfo.workers << " of "
                  << runInfo.hardwareThreads << " threads (" << compilerName() << ", "
                  << buildType() << ")\n";

        if (argc > 4)                                   // argv[4] exists only when argc > 4
            writeResultsJson(argv[4], result, spinCount, seed, runInfo, wallSeconds,
                             mode, sessionsMode ? triggerRate : 0.0);

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