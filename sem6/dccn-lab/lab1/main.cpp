#include <iostream>
#include <string>
using namespace std;

string xorDivide(string data, string divisor)
{
    int n = divisor.length();

    for (int i = 0; i <= data.length() - n; i++)
        if (data[i] == '1')
            for (int j = 0; j < n; j++)
                data[i + j] = (data[i + j] == divisor[j]) ? '0' : '1';
    return data.substr(data.length() - (n - 1));
}

int main()
{
    string data = "101110";
    string divisor = "1001"; // x^3 + 1

    int degree = divisor.length() - 1;
    string appendedData = data + string(degree, '0');
    string crc = xorDivide(appendedData, divisor);
    string codeword = data + crc;

    cout << "Data: " << data << endl;
    cout << "Divisor: " << divisor << endl;
    cout << "CRC: " << crc << endl;
    cout << "CRC Codeword: " << codeword << endl;

    return 0;
}

