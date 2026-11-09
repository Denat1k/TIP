#include <algorithm>
#include <climits>
#include <iostream>
#include <vector>

int main()
{
    int plantCount, bouquetSize, maxSame;
    std::cin >> plantCount >> bouquetSize >> maxSame;
    std::vector<long long> price(plantCount);
    for (auto& value : price)
        std::cin >> value;

    const long long NONE = LLONG_MIN;
    std::vector<long long> dp(bouquetSize + 1, NONE);
    dp[0] = 0;
    for (long long cost : price) {
        std::vector<long long> next = dp;
        for (int k = 0; k <= bouquetSize; ++k) {
            if (dp[k] == NONE)
                continue;
            for (int take = 1; take <= maxSame && k + take <= bouquetSize; ++take)
                next[k + take] = std::max(next[k + take], dp[k] + take * cost);
        }
        dp = next;
    }

    if (dp[bouquetSize] == NONE)
        std::cout << "Собрать букет невозможно" << std::endl;
    else
        std::cout << dp[bouquetSize] << std::endl;
    return 0;
}
