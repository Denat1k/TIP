// Практическое занятие №8, задача №1. Быстрое возведение в степень.
// Клоков Иван Николаевич, ЭФБО-07-26
// Число умножений ~ log2(n): на каждом шаге степень делится пополам.
#include <iostream>

// Возводит base в степень exponent (exponent >= 0) за O(log n)
unsigned long long fastPower(unsigned long long base, unsigned long long exponent)
{
    unsigned long long result = 1;
    while (exponent > 0) {
        if (exponent % 2 == 1)   // текущий двоичный разряд степени = 1
            result *= base;
        base *= base;            // base^1, base^2, base^4, ...
        exponent /= 2;
    }
    return result;
}

int main()
{
    unsigned long long base, exponent;
    std::cin >> base >> exponent;
    std::cout << fastPower(base, exponent) << std::endl;
    return 0;
}
