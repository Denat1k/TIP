// Практическое занятие №11, задача №2. Пирожки по дням.
// Клоков Иван Николаевич, ЭФБО-07-26
//
// Нужно минимизировать наибольшую (по всем дням) разницу калорий внутри дня.
// После сортировки в каждый день выгодно брать подряд идущие пирожки.
// dp[d][i] - лучший ответ, если первые i пирожков разложены на d дней:
//   dp[d][i] = min по j (d-1 <= j < i) от max(dp[d-1][j], a[i-1] - a[j]).
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
    previous[0] = 0;  // 0 пирожков на 0 дней
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
