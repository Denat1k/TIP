#include <algorithm>
#include <climits>
#include <iostream>
#include <vector>

int main()
{
    int count, days;
    std::cin >> count >> days;
    std::vector<long long> calories(count);
    for (auto& value : calories)
        std::cin >> value;
    std::sort(calories.begin(), calories.end());

    const long long INF = LLONG_MAX;
    std::vector<long long> previous(count + 1, INF), current(count + 1, INF);
    previous[0] = 0;
    for (int d = 1; d <= days; ++d) {
        std::fill(current.begin(), current.end(), INF);
        for (int i = d; i <= count; ++i)
            for (int j = d - 1; j < i; ++j)
                if (previous[j] != INF)
                    current[i] = std::min(current[i],
                                          std::max(previous[j], calories[i - 1] - calories[j]));
        std::swap(previous, current);
    }
    std::cout << previous[count] << std::endl;
    return 0;
}
