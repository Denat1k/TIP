#include <cctype>
#include <fstream>
#include <iostream>
#include <string>

bool isForbidden(char symbol)
{
    const std::string forbidden = "useragreement";
    char lower = static_cast<char>(std::tolower(static_cast<unsigned char>(symbol)));
    return forbidden.find(lower) != std::string::npos;
}

int main()
{
    std::ifstream input("input.txt");
    std::ofstream output("output.txt");
    if (!input) {
        std::cout << "Не удалось открыть input.txt" << std::endl;
        return 1;
    }

    char symbol;
    while (input.get(symbol))
        if (!isForbidden(symbol))
            output << symbol;
    return 0;
}
