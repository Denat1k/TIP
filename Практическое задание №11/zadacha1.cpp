// Практическое занятие №11, задача №1. Маршрут с максимальной суммой баллов
// из левого верхнего угла в правый нижний (ходы только вниз и вправо).
// Клоков Иван Николаевич, ЭФБО-07-26
// Ввод: N M, затем N строк по M чисел. Вывод: координаты клеток маршрута.
#include <iostream>
#include <vector>

int main()
{
    int rows, cols;
    std::cin >> rows >> cols;
    std::vector<std::vector<long long>> points(rows, std::vector<long long>(cols));
    for (auto& row : points)
        for (auto& value : row)
            std::cin >> value;

    // best[i][j] - максимальная сумма, с которой можно прийти в клетку (i, j)
    std::vector<std::vector<long long>> best(rows, std::vector<long long>(cols));
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            best[i][j] = points[i][j];
            if (i == 0 && j > 0)
                best[i][j] += best[i][j - 1];
            else if (j == 0 && i > 0)
                best[i][j] += best[i - 1][j];
            else if (i > 0 && j > 0)
                best[i][j] += std::max(best[i - 1][j], best[i][j - 1]);
        }
    }

    // Восстанавливаем маршрут с конца: идём туда, откуда пришёл максимум
    std::vector<std::pair<int, int>> path;
    int i = rows - 1, j = cols - 1;
    while (true) {
        path.push_back({i, j});
        if (i == 0 && j == 0)
            break;
        if (i == 0)
            --j;
        else if (j == 0)
            --i;
        else if (best[i - 1][j] >= best[i][j - 1])
            --i;
        else
            --j;
    }

    std::cout << "Сумма баллов: " << best[rows - 1][cols - 1] << "\n";
    for (auto it = path.rbegin(); it != path.rend(); ++it)
        std::cout << it->first << ' ' << it->second << "\n";
    return 0;
}
