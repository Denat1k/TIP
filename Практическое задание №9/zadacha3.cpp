#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <string>

int divideByTwo(std::string& number)
{
    std::string quotient;
    int carry = 0;
    for (char digit : number) {
        int current = carry * 10 + (digit - '0');
        quotient += static_cast<char>('0' + current / 2);
        carry = current % 2;
    }
    size_t firstNonZero = quotient.find_first_not_of('0');
    number = firstNonZero == std::string::npos ? "0" : quotient.substr(firstNonZero);
    return carry;
}

std::string toBinary(std::string number)
{
    if (number == "0")
        return "0";
    std::string binary;
    while (number != "0")
        binary += static_cast<char>('0' + divideByTwo(number));
    std::reverse(binary.begin(), binary.end());
    return binary;
}

int main()
{
    std::ifstream input("input.txt");
    if (!input) {
        std::cout << "Не удалось открыть input.txt" << std::endl;
        return 1;
    }
    std::string line, result;
    std::getline(input, line);

    for (size_t i = 0; i < line.size();) {
        if (std::isdigit(static_cast<unsigned char>(line[i]))) {
            size_t end = i;
            while (end < line.size() && std::isdigit(static_cast<unsigned char>(line[end])))
                ++end;
            result += toBinary(line.substr(i, end - i));
            i = end;
        } else {
            result += line[i++];
        }
    }
    std::ofstream("output.txt") << result;
    return 0;
}
