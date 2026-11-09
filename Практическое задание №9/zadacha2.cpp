// Практическое занятие №9, задача №2. Является ли Y подстрокой X.
// Клоков Иван Николаевич, ЭФБО-07-26
// X читается из input1.txt, Y - из input2.txt.
#include <fstream>
#include <iostream>
#include <string>

// Читает первую строку файла; false, если файл не открылся
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
