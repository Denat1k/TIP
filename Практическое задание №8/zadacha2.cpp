// Практическое занятие №8, задача №2. Сумма сброса = НОД(a, b).
// Клоков Иван Николаевич, ЭФБО-07-26
#include <iostream>

// Рекурсивный алгоритм Евклида
long long gcd(long long a, long long b)
{
    if (b == 0)
        return a;
    return gcd(b, a % b);
}

int main()
{
    long long a, b;
    std::cin >> a >> b;
    std::cout << gcd(a, b) << std::endl;
    return 0;
}
