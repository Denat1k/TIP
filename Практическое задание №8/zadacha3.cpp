#include <iostream>

void moveIngredients(int n, int from, int to, int spare)
{
    if (n == 0)
        return;
    moveIngredients(n - 1, from, spare, to);
    std::cout << "Ingredient " << n << " move from " << from << " to " << to << "\n";
    moveIngredients(n - 1, spare, to, from);
}

int main()
{
    int n;
    std::cin >> n;
    moveIngredients(n, 1, 3, 2);
    return 0;
}
