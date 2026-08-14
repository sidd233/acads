int binarySearch(int arr[], int n, int target) {
    int low = 0;
    int high = n - 1;
    while (low <= high) {
        int mid = (low + high) / 2;
        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    return -1;
}

int validateAndSum(int arr[], int n) {
    int sum = 0;
    int i = 0;
    if (n <= 0) {
        goto error;
    }
    for (i = 0; i < n; i++) {
        if (arr[i] < 0) {
            goto error;
        }
        sum += arr[i];
    }
    return sum;

error:
    return -1;
}

int collatzSteps(int n) {
    int steps = 0;
    do {
        if (n % 2 == 0) {
            n = n / 2;
        } else {
            n = 3 * n + 1;
        }
        steps++;
    } while (n != 1);
    return steps;
}

char categorize(int score) {
    char grade;
    switch (score / 10) {
        case 10:
        case 9:
        case 8:
            grade = 'A';
            break;
        case 7:
        case 6:
            grade = 'B';
            break;
        case 5:
            grade = 'C';
            break;
        default:
            grade = 'F';
    }
    return grade;
}

int gcd(int a, int b) {
    while (b != 0) {
        int t = b;
        b = a % b;
        a = t;
    }
    return a;
}

int matrixTrace(int m[], int n) {
    int trace = 0;
    int i = 0;
    int j = 0;
    for (i = 0; i < n; i++) {
        for (j = 0; j < n; j++) {
            if (i == j) {
                trace += m[i * n + j];
            }
        }
    }
    return trace;
}
