#pragma once
#include <iostream>
#include <string>
#include <algorithm>  
#include <cctype>     
#include <iomanip>
#include <random>
#include <unordered_map>


namespace Utility {

    inline void Print(char* value) {
        std::cout << value << std::endl;
    }
    inline void Print(const char* value) {
        std::cout << value << std::endl;
    }
    inline void Print(int value) {
        std::cout << value << std::endl;
    }
    inline void Print(float value) {
        std::cout << value << std::endl;
    }
    inline void Print(std::string value) {
        std::cout << value << std::endl;
    }
    inline void Print(bool value) {
        std::cout << value << std::endl;
    }


    // Returns a random int in [min, max] — both endpoints inclusive
    inline int randomInt(int min, int max) {
        static thread_local std::mt19937 rng(std::random_device{}());
        std::uniform_int_distribution<int> dist(min, max);
        return dist(rng);
    }

    template <typename Key, typename Weight>
    inline Key pickRandomFromDict(const std::unordered_map<Key, Weight>& weights) {
        static thread_local std::mt19937 rng(std::random_device{}());

        std::vector<Key>    keys;
        std::vector<double> vals;
        keys.reserve(weights.size());
        vals.reserve(weights.size());
        for (const auto& [k, w] : weights) {
            keys.push_back(k);
            vals.push_back(static_cast<double>(w));
        }

        std::discrete_distribution<std::size_t> dist(vals.begin(), vals.end());
        return keys[dist(rng)];
    }

    inline std::vector<std::string> getOrderedKeys(const std::unordered_map<std::string, double>&) {
        return {
            "0-1", "1-2", "2-3", "3-5", "5-10", "10-20", "20-50",
            "50-100", "100-200", "200-300", "300-500",
            "500-600", "600-700", "700-"
        };
    }

    inline void printWinDistribution(const std::unordered_map<std::string, double>& winDistribution) {
        const auto order = getOrderedKeys(winDistribution);

        double total = 0;
        for (const auto& key : order)
            total += winDistribution.count(key) ? winDistribution.at(key) : 0;

        std::cout << "\n====== Win Distribution ======\n";
        std::cout << std::left
            << std::setw(12) << "Range"
            << std::setw(10) << "Count"
            << std::setw(10) << "%"
            << "\n";
        std::cout << std::string(32, '-') << "\n";

        std::cout << std::fixed << std::setprecision(2);   // set once; sticky for the rest
        for (const auto& key : order) {
            double count = winDistribution.count(key) ? winDistribution.at(key) : 0;
            double pct = (total > 0) ? (count / total * 100.0) : 0.0;

            std::cout << std::left
                << std::setw(12) << key
                << std::setw(10) << static_cast<long long>(count)
                << std::setw(9) << pct << "%\n";
        }

        std::cout << std::string(32, '-') << "\n";
        std::cout << std::left
            << std::setw(12) << "Total"
            << std::setw(10) << static_cast<long long>(total)
            << "\n";
        std::cout << "==============================\n\n";
    }
}