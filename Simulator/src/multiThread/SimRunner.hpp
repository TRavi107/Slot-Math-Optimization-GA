#pragma once

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <future>
#include <iostream>
#include <optional>
#include <string>
#include <thread>
#include <vector>

#include "../Utility/Rng.hpp"

namespace SimRunner {
    //
    // The runner is generic over an "accumulator" type. The caller supplies:
    //
    //   Result       any type that supports `Result& operator+=(const Result&)`
    //
    //   MakeResult   a callable `Result(long long spins)` that returns a fresh,
    //                correctly-sized accumulator.
    //
    //   RunSim       a callable `void(long long spins, Result&, Rng::Xoshiro256ss&)`
    //                that runs `spins` spins using the given RNG and accumulates
    //                the outcome directly into the accumulator.
    //
    // REPRODUCIBILITY
    //   The work is cut into fixed-size jobs (JOB_SPINS). Job j always uses the
    //   RNG seeded with Rng::jobSeed(seed, j), and job results are merged in job
    //   order. So the result depends only on (seed, spinCount) — never on the
    //   number of CPU cores or on which thread happened to run which job.
    //   (The timing in RunInfo does depend on the machine; it is not part of the result.)
    // ─────────────────────────────────────────────

    constexpr long long JOB_SPINS = 1'000'000;   // fixed: changing it changes results

    // What one call cost: filled in by RunMultiThreadSim when `info` is given.
    struct RunInfo {
        int workers = 0;            // worker threads actually used
        int hardwareThreads = 0;    // logical CPUs the OS reports
        long long jobs = 0;         // JOB_SPINS-sized jobs
        double seconds = 0.0;       // wall time from launching workers to the merged result
    };

    // Worker threads a run of `spinCount` spins uses: 80% of the logical CPUs
    // (leaves the machine usable), never more than there are jobs.
    inline int workerCount(long long spinCount, int workerOverride = 0) {
        const long long jobCount = (spinCount + JOB_SPINS - 1) / JOB_SPINS;
        int hwThreads = static_cast<int>(std::thread::hardware_concurrency());
        int workers = std::max(1, static_cast<int>(std::floor(hwThreads * 0.8)));
        if (workerOverride > 0) workers = workerOverride;
        return static_cast<int>(std::max(1LL, std::min<long long>(workers, jobCount)));
    }

    // ─────────────────────────────────────────────
    // Progress bar printer
    // ─────────────────────────────────────────────
    inline void print_progress(long long completed, long long total) {
        int percent = static_cast<int>((static_cast<double>(completed) / total) * 100);
        int filled = percent / 5;   // 20 blocks = 100%
        std::string asciiBar = std::string(filled, '#') + std::string(20 - filled, '-');
        std::cout << "  [" << asciiBar << "] " << percent << "%"
            << "  (" << completed << "/" << total << " spins)" << std::flush << "\r";
    }

    // ─────────────────────────────────────────────
    // Multi-threaded, deterministic simulation runner
    // workerOverride > 0 fixes the thread count (results stay identical).
    // ─────────────────────────────────────────────
    template <typename Result, typename MakeResult, typename RunSim>
    inline Result RunMultiThreadSim(const long long spinCount, const uint64_t seed,
                                    MakeResult makeResult, RunSim runSim,
                                    int workerOverride = 0, RunInfo* info = nullptr) {
        const auto t0 = std::chrono::steady_clock::now();
        const long long jobCount = (spinCount + JOB_SPINS - 1) / JOB_SPINS;
        const int workers = workerCount(spinCount, workerOverride);

        // One slot per job; each slot is written by exactly one thread.
        std::vector<std::optional<Result>> jobResults(static_cast<size_t>(jobCount));
        std::atomic<long long> nextJob{ 0 };
        std::atomic<long long> spinsDone{ 0 };

        auto worker = [&]() {
            for (long long j; (j = nextJob.fetch_add(1)) < jobCount; ) {
                const long long spins = std::min(JOB_SPINS, spinCount - j * JOB_SPINS);
                Rng::Xoshiro256ss rng(Rng::jobSeed(seed, static_cast<uint64_t>(j)));

                Result r = makeResult(spins);
                runSim(spins, r, rng);

                jobResults[static_cast<size_t>(j)].emplace(std::move(r));
                spinsDone.fetch_add(spins, std::memory_order_relaxed);
            }
        };

        // ── Launch workers (futures so exceptions reach the caller) ──
        std::vector<std::future<void>> futures;
        futures.reserve(workers);
        for (int i = 0; i < workers; ++i)
            futures.push_back(std::async(std::launch::async, worker));

        // ── Progress monitor ──────────────────────────────────────────
        auto allDone = [&]() {
            for (auto& f : futures)
                if (f.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready)
                    return false;
            return true;
        };

        int lastPrinted = -1;
        while (!allDone()) {
            const long long done = spinsDone.load(std::memory_order_relaxed);
            const int milestone = static_cast<int>(100.0 * done / spinCount) / 10 * 10;
            if (milestone > lastPrinted) {
                lastPrinted = milestone;
                print_progress(done, spinCount);
                std::cout << "\n";
            }
            // short poll: a 10M-spin call can finish in well under a second, and a
            // long sleep here would be counted as simulation time
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
        for (auto& f : futures) f.get();       // rethrows any worker exception

        print_progress(spinCount, spinCount);
        std::cout << "\n";

        // ── Merge in job order — fixed floating-point summation order ─
        Result finalSim = makeResult(spinCount);
        for (auto& r : jobResults)
            finalSim += *r;

        if (info) {
            info->workers = workers;
            info->hardwareThreads = static_cast<int>(std::thread::hardware_concurrency());
            info->jobs = jobCount;
            info->seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
        }
        return finalSim;
    }
}
