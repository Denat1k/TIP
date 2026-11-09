// Практическое занятие №8, задача №3. Перекладывание ингредиентов
// (задача о Ханойской башне) с салфетки 1 на салфетку 3.
// Клоков Иван Николаевич, ЭФБО-07-26
#include <iostream>

// Переносит n верхних ингредиентов с салфетки from на салфетку to через spare
void moveIngredients(int n, int from, int to, int spare)
{
    if (n == 0)
        return;
    moveIngredients(n - 1, from, spare, to);   // убираем n-1 меньших на запасную
    std::cout << "Ingredient " << n << " move from " << from << " to " << to << "\n";
    moveIngredients(n - 1, spare, to, from);   // кладём их обратно сверху
}

int main()
{
    int n;
    std::cin >> n;
    moveIngredients(n, 1, 3, 2);
    return 0;
}
