#include <stdio.h>

int classify(int x) {
    int result = 0;
    if (x < 0) {
        result = -1;
    } else if (x == 0) {
        result = 0;
    } else {
        result = 1;
    }
    return result;
}

int sumEvens(int n) {
    int i;
    int sum = 0;
    for (i = 0; i < n; i++) {
        if (i % 2 != 0) {
            continue;
        }
        sum += i;
    }
    return sum;
}

int gradeOf(int score) {
    int grade;
    switch (score / 10) {
        case 10:
        case 9:
            grade = 'A';
            break;
        case 8:
            grade = 'B';
            break;
        case 7:
            grade = 'C';
            break;
        default:
            grade = 'F';
    }
    return grade;
}

int findFirstNegative(int arr[], int n) {
    int i = 0;
    while (i < n) {
        if (arr[i] < 0) {
            return i;
        }
        i++;
    }
    return -1;
}
