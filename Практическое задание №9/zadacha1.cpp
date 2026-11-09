// Практическое занятие №9, задача №1. Удаление букв фразы "user agreement".
// Клоков Иван Николаевич, ЭФБО-07-26
// Вход: input.txt, выход: output.txt
#include <cctype>
#include <fstream>
#include <iostream>
#include <string>

// true, если символ - буква из "user agreement" (без учёта регистра)
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

    // Посимвольно копируем всё, кроме запрещённых букв
    char symbol;
    while (input.get(symbol))
        if (!isForbidden(symbol))
            output << symbol;
    return 0;
}
