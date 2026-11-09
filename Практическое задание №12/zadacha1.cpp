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
            std::cin >> cell;

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
