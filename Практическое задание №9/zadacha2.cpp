#include <fstream>
#include <iostream>
#include <string>

bool readLine(const std::string& fileName, std::string& line)
{
    std::ifstream file(fileName);
    if (!file)
        return false;
    std::getline(file, line);
    return true;
}

int main()
{
    std::string carlin, prodolny;
    if (!readLine("input1.txt", carlin) || !readLine("input2.txt", prodolny)) {
        std::cout << "Не удалось открыть входные файлы" << std::endl;
        return 1;
    }
    std::cout << (carlin.find(prodolny) != std::string::npos ? "yes" : "no") << std::endl;
    return 0;
}
