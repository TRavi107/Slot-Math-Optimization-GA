#pragma once
#include <cstdint>

// ─────────────────────────────────────────────
// Deterministic, portable RNG used by the whole simulator.
// Same seed -> same sequence on every compiler / OS / CPU
// (unlike std::uniform_int_distribution, whose output is implementation-defined).
// ─────────────────────────────────────────────
namespace Rng {

    struct Xoshiro256ss {
        uint64_t s[4];

        static uint64_t splitmix(uint64_t& x) {
            uint64_t z = (x += 0x9E3779B97F4A7C15ULL);
            z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
            z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
            return z ^ (z >> 31);
        }

        explicit Xoshiro256ss(uint64_t seed) { for (auto& v : s) v = splitmix(seed); }

        static inline uint64_t rotl(uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }

        inline uint64_t next() {
            const uint64_t result = rotl(s[1] * 5, 7) * 9;
            const uint64_t t = s[1] << 17;
            s[2] ^= s[0]; s[3] ^= s[1]; s[1] ^= s[2]; s[0] ^= s[3];
            s[2] ^= t; s[3] = rotl(s[3], 45);
            return result;
        }

        // uniform in [0, n), no division; bias is ~n/2^32, negligible for n = 50
        inline uint32_t bounded(uint32_t n) {
            return (uint32_t)(((next() >> 32) * (uint64_t)n) >> 32);
        }
    };

    // Seed for job `job` of a run started with `seed`.
    // Hashed, so consecutive jobs get unrelated generator states.
    inline uint64_t jobSeed(uint64_t seed, uint64_t job) {
        uint64_t x = seed ^ (job * 0xD1B54A32D192ED03ULL);
        return Xoshiro256ss::splitmix(x);
    }
}