#include <iostream>

unsigned long long fastPower(unsigned long long base, unsigned long long exponent)
{
    unsigned long long result = 1;
    while (exponent > 0) {
        if (exponent % 2 == 1)
            result *= base;
        base *= base;
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
