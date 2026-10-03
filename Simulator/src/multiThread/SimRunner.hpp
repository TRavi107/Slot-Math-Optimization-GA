#pragma once

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <future>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

namespace SimRunner {
    //
    // The runner is generic over an "accumulator" type. The caller supplies:
    //
    //   Result       any type that supports `Result& operator+=(const Result&)`
    //
    //   MakeResult   a callable `Result(int spins)` that returns a fresh,
    //                correctly-sized accumulator. This is where all the
    //                type-specific construction (baseBet, maxWin, the matrix
    //                data, etc.) now lives — on the caller's side.
    //
    //   RunSim       a callable `void(long batch, Result&)` that runs `batch`
    //                spins and accumulates the outcome directly into the
    //                accumulator (zero temporaries).
    // ─────────────────────────────────────────────

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
    // Run a chunk of spins in one worker.
    // Reports progress via a shared atomic counter.
    // ─────────────────────────────────────────────
    template <typename Result, typename MakeResult, typename RunSim>
    inline Result runSim_chunked(int spins,
        std::atomic<int>& progressCounter,
        MakeResult makeResult,
        RunSim runSim) {
        Result result = makeResult(spins);   // caller-provided construction

        int milestoneSize = std::max(1, spins / 10);
        int remaining = spins;
        int done = 0;
        int nextMilestone = milestoneSize;

        while (remaining > 0) {
            int batch = std::min(milestoneSize, remaining);
            runSim(batch, result);   // accumulate directly — zero allocation

            done += batch;
            remaining -= batch;

            if (done >= nextMilestone) {
                progressCounter.fetch_add(1, std::memory_order_relaxed);
                nextMilestone += milestoneSize;
            }
        }

        progressCounter.fetch_add(1, std::memory_order_relaxed);
        return result;
    }

    // ─────────────────────────────────────────────
    // Multi-threaded simulation runner
    // Uses std::thread + std::future (true parallelism).
    // ─────────────────────────────────────────────
    template <typename Result, typename MakeResult, typename RunSim>
    inline Result RunMultiThreadSim(const long long spinCount , MakeResult makeResult,RunSim runSim) {
        int hwThreads = static_cast<int>(std::thread::hardware_concurrency());
        int maxWorkers = std::max(1, static_cast<int>(std::floor(hwThreads * 0.8)));
        //maxWorkers = 1;
        long spinsPerWorker = spinCount / maxWorkers;
        long remainder = spinCount % maxWorkers;
        std::atomic<int> progressCounter{ 0 };
        int totalReports = maxWorkers * 10;

        // ── Launch workers ────────────────────────────────────────────
        std::vector<std::future<Result>> futures;
        futures.reserve(maxWorkers);

        for (int i = 0; i < maxWorkers; ++i) {
            int chunk = spinsPerWorker + (i < remainder ? 1 : 0);

            // makeResult / runSim are captured by value so each worker owns an
            // independent copy — no shared state, no races on the callables.
            futures.push_back(std::async(std::launch::async,
                [chunk, &progressCounter, makeResult, runSim]() -> Result {

                    // Each thread has its own accumulator — no sharing
                    Result result = makeResult(chunk);

                    int milestoneSize = std::max(1, chunk / 10);
                    int remaining = chunk;
                    int done = 0;
                    int nextMilestone = milestoneSize;

                    while (remaining > 0) {
                        int batch = std::min(milestoneSize, remaining);

                        // Accumulate directly into result — no temporaries
                        runSim(batch, result);

                        done += batch;
                        remaining -= batch;

                        if (done >= nextMilestone) {
                            progressCounter.fetch_add(1, std::memory_order_relaxed);
                            nextMilestone += milestoneSize;
                        }
                    }

                    progressCounter.fetch_add(1, std::memory_order_relaxed);
                    return result;
                }));
        }

        // ── Progress monitor ──────────────────────────────────────────
        int lastPrinted = -1;
        while (true) {
            int completed = progressCounter.load(std::memory_order_relaxed);
            if (completed >= totalReports) break;

            int percent = static_cast<int>((static_cast<double>(completed) / totalReports) * 100);
            int milestone = (percent / 10) * 10;

            if (milestone > lastPrinted) {
                lastPrinted = milestone;
                long long done = static_cast<long long>(
                    static_cast<double>(completed) / totalReports * spinCount);
                print_progress(done, spinCount);
                std::cout << "\n";
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }

        print_progress(spinCount, spinCount);
        std::cout << "\n";

        // ── Merge all thread results into final — sequential, no race ─
        Result finalSim = makeResult(spinCount);
        for (auto& f : futures)
            finalSim += f.get();

        return finalSim;
    }
}