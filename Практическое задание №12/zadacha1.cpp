// Практическое занятие №12, задача №1. Лабиринт с pdf-файлами.
// Клоков Иван Николаевич, ЭФБО-07-26
//
// Условие не задаёт старт и правила движения, поэтому, как в практике №11:
// старт - левая верхняя клетка, ходы только вправо и вниз.
// Ввод: N M, затем N строк по M символов (0 - пусто, 1 - стена, P - pdf, E - выход),
// пробелы между символами допускаются.
// Вывод: максимум pdf на пути к выходу или -1, если выход недостижим.
#include <algorithm>
#include <iostream>
#include <vector>

int main()
{
    int rows, cols;
    std::cin >> rows >> cols;
    std::vector<std::vector<char>> maze(rows, std::vector<char>(cols));
    for (auto& row : maze)
        for (char& cell : row)
            std::cin >> cell;  // >> пропускает пробелы и переводы строк

    // collected[i][j] - максимум pdf, с которым можно дойти до (i, j); -1 - недостижимо
    const int UNREACHABLE = -1;
    std::vector<std::vector<int>> collected(rows, std::vector<int>(cols, UNREACHABLE));
    int answer = UNREACHABLE;
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            if (maze[i][j] == '1')
                continue;
            int best = (i == 0 && j == 0) ? 0 : UNREACHABLE;
            if (i > 0)
                best = std::max(best, collected[i - 1][j]);
            if (j > 0)
                best = std::max(best, collected[i][j - 1]);
            if (best == UNREACHABLE)
                continue;
            collected[i][j] = best + (maze[i][j] == 'P' ? 1 : 0);
            if (maze[i][j] == 'E')
                answer = std::max(answer, collected[i][j]);
        }
    }
    std::cout << answer << std::endl;
    return 0;
}
