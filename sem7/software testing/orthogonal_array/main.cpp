#include <iostream>
#include <vector>
#include <stdexcept>
#include <algorithm>
#include <cmath>
#include <cstdint>

using namespace std;

using ll = long long;

// ============================================================
// Basic number theory
// ============================================================

bool isPrime(int n) {
    if (n < 2) return false;

    for (int d = 2; 1LL * d * d <= n; ++d) {
        if (n % d == 0)
            return false;
    }

    return true;
}

ll intPow(ll a, int b) {
    ll result = 1;

    while (b--) {
        result *= a;
    }

    return result;
}

// Factor n into prime powers.
//
// Example:
//      12 = 4 * 3
//      18 = 2 * 9
//      60 = 4 * 3 * 5
//
vector<int> primePowerFactors(int n) {
    vector<int> factors;

    for (int prime = 2; 1LL * prime * prime <= n; ++prime) {
        if (n % prime != 0)
            continue;

        int power = 1;

        while (n % prime == 0) {
            n /= prime;
            power *= prime;
        }

        factors.push_back(power);
    }

    if (n > 1)
        factors.push_back(n);

    return factors;
}

// Given q = prime^degree, recover prime and degree.
pair<int, int> getPrimeAndDegree(int q) {
    for (int p = 2; p <= q; ++p) {

        if (!isPrime(p))
            continue;

        int value = 1;

        for (int degree = 1; value <= q; ++degree) {
            value *= p;

            if (value == q)
                return {p, degree};

            if (value > q)
                break;
        }
    }

    throw runtime_error("Not a prime power");
}

// ============================================================
// Polynomial utilities over GF(p)
// ============================================================

int mod(int x, int p) {
    x %= p;

    if (x < 0)
        x += p;

    return x;
}

void trim(vector<int>& a) {
    while (a.size() > 1 && a.back() == 0)
        a.pop_back();
}

// Polynomial remainder a(x) mod b(x)
//
// b is assumed monic.
//
vector<int> polynomialRemainder(
    vector<int> a,
    const vector<int>& b,
    int p
) {
    trim(a);

    int degB = (int)b.size() - 1;

    while ((int)a.size() - 1 >= degB &&
           !(a.size() == 1 && a[0] == 0)) {

        int degA = (int)a.size() - 1;
        int shift = degA - degB;

        int coefficient = a.back();

        for (int i = 0; i <= degB; ++i) {
            a[i + shift] =
                mod(a[i + shift] - coefficient * b[i], p);
        }

        trim(a);
    }

    return a;
}

// Evaluate polynomial at x in GF(p)
int evaluatePolynomial(
    const vector<int>& poly,
    int x,
    int p
) {
    int result = 0;

    for (int i = (int)poly.size() - 1; i >= 0; --i) {
        result = mod(result * x + poly[i], p);
    }

    return result;
}

// ------------------------------------------------------------
// Check whether a monic polynomial is irreducible.
//
// For the small finite fields normally used in Orthogonal Array
// Testing this brute-force approach is sufficient.
//
// We test whether the polynomial is divisible by any monic
// polynomial of degree <= degree/2.
// ------------------------------------------------------------

bool isIrreducible(const vector<int>& poly, int p) {
    int degree = (int)poly.size() - 1;

    if (degree == 1)
        return true;

    for (int divisorDegree = 1;
         divisorDegree <= degree / 2;
         ++divisorDegree) {

        ll combinations = intPow(p, divisorDegree);

        for (ll code = 0; code < combinations; ++code) {

            vector<int> divisor(divisorDegree + 1);

            ll temp = code;

            for (int i = 0; i < divisorDegree; ++i) {
                divisor[i] = temp % p;
                temp /= p;
            }

            // monic polynomial
            divisor[divisorDegree] = 1;

            // Constant term 0 means divisible by x,
            // so skip it.
            if (divisor[0] == 0)
                continue;

            vector<int> rem =
                polynomialRemainder(poly, divisor, p);

            bool zero = true;

            for (int x : rem) {
                if (x != 0) {
                    zero = false;
                    break;
                }
            }

            if (zero)
                return false;
        }
    }

    return true;
}

// Find a monic irreducible polynomial of the requested degree
// over GF(p).
vector<int> findIrreduciblePolynomial(int p, int degree) {

    if (degree == 1)
        return {0, 1};

    ll possibilities = intPow(p, degree);

    for (ll code = 0; code < possibilities; ++code) {

        vector<int> poly(degree + 1);

        ll temp = code;

        for (int i = 0; i < degree; ++i) {
            poly[i] = temp % p;
            temp /= p;
        }

        // monic
        poly[degree] = 1;

        // Must have non-zero constant term.
        if (poly[0] == 0)
            continue;

        if (isIrreducible(poly, p))
            return poly;
    }

    throw runtime_error(
        "Could not find irreducible polynomial."
    );
}

// ============================================================
// Finite field GF(q)
// ============================================================
//
// q = p^r
//
// Field elements are represented by integers:
//
//      0, 1, ..., q-1
//
// Internally, an integer represents a polynomial of degree
// less than r.
//
// Example GF(4):
//
//      0 -> 0
//      1 -> 1
//      2 -> x
//      3 -> x + 1
//
// ============================================================

class FiniteField {

private:

    int p;
    int degree;
    int q;

    vector<int> irreducible;

    vector<int> toCoefficients(int value) const {

        vector<int> result(degree);

        for (int i = 0; i < degree; ++i) {
            result[i] = value % p;
            value /= p;
        }

        return result;
    }

    int fromCoefficients(const vector<int>& a) const {

        int result = 0;
        int multiplier = 1;

        for (int i = 0; i < degree; ++i) {
            result += a[i] * multiplier;
            multiplier *= p;
        }

        return result;
    }

public:

    explicit FiniteField(int primePower) {

        q = primePower;

        auto [prime, deg] =
            getPrimeAndDegree(primePower);

        p = prime;
        degree = deg;

        irreducible =
            findIrreduciblePolynomial(p, degree);
    }

    int size() const {
        return q;
    }

    int add(int a, int b) const {

        vector<int> A = toCoefficients(a);
        vector<int> B = toCoefficients(b);

        vector<int> C(degree);

        for (int i = 0; i < degree; ++i) {
            C[i] = (A[i] + B[i]) % p;
        }

        return fromCoefficients(C);
    }

    int multiply(int a, int b) const {

        if (a == 0 || b == 0)
            return 0;

        vector<int> A = toCoefficients(a);
        vector<int> B = toCoefficients(b);

        vector<int> product(2 * degree - 1, 0);

        // Polynomial multiplication
        for (int i = 0; i < degree; ++i) {
            for (int j = 0; j < degree; ++j) {

                product[i + j] =
                    mod(
                        product[i + j]
                        + A[i] * B[j],
                        p
                    );
            }
        }

        // Reduce modulo the irreducible polynomial
        for (int d = 2 * degree - 2;
             d >= degree;
             --d) {

            int coefficient = product[d];

            if (coefficient == 0)
                continue;

            int shift = d - degree;

            for (int i = 0; i < degree; ++i) {

                product[i + shift] =
                    mod(
                        product[i + shift]
                        - coefficient * irreducible[i],
                        p
                    );
            }
        }

        product.resize(degree);

        return fromCoefficients(product);
    }
};

// ============================================================
// Vector utilities over GF(q)
// ============================================================

vector<int> numberToVector(
    ll number,
    int dimension,
    int q
) {
    vector<int> result(dimension);

    for (int i = 0; i < dimension; ++i) {
        result[i] = number % q;
        number /= q;
    }

    return result;
}

// Normalize a non-zero vector.
//
// We don't actually need division.
//
// We find the first non-zero coordinate and enumerate only
// vectors whose first non-zero coordinate is 1.
//
// This gives exactly one representative from each
// one-dimensional subspace.
bool isCanonicalDirection(const vector<int>& v) {

    for (int x : v) {

        if (x != 0)
            return x == 1;
    }

    return false;
}

int dotProduct(
    const vector<int>& a,
    const vector<int>& b,
    const FiniteField& field
) {
    int result = 0;

    for (int i = 0; i < (int)a.size(); ++i) {

        result = field.add(
            result,
            field.multiply(a[i], b[i])
        );
    }

    return result;
}

// ============================================================
// Construct OA(q^d, k, q, 2)
// ============================================================

vector<vector<int>> generatePrimePowerOA(
    int factors,
    int q
) {
    FiniteField field(q);

    // --------------------------------------------------------
    // Find the smallest d such that
    //
    //        (q^d - 1)/(q - 1) >= factors
    //
    // --------------------------------------------------------

    int dimension = 1;
    ll rows = q;

    while ((rows - 1) / (q - 1) < factors) {

        if (rows > 10000000LL / q) {
            throw runtime_error(
                "Required orthogonal array is too large."
            );
        }

        rows *= q;
        dimension++;
    }

    // --------------------------------------------------------
    // Generate canonical directions.
    // --------------------------------------------------------

    vector<vector<int>> directions;

    for (ll code = 1;
         code < rows &&
         (int)directions.size() < factors;
         ++code) {

        vector<int> v =
            numberToVector(code, dimension, q);

        if (isCanonicalDirection(v)) {
            directions.push_back(v);
        }
    }

    if ((int)directions.size() < factors) {
        throw runtime_error(
            "Could not generate enough directions."
        );
    }

    // --------------------------------------------------------
    // Generate the OA.
    //
    // Every vector x in GF(q)^d becomes one row.
    //
    // Column j contains:
    //
    //             x dot v_j
    //
    // --------------------------------------------------------

    vector<vector<int>> OA(
        rows,
        vector<int>(factors)
    );

    for (ll r = 0; r < rows; ++r) {

        vector<int> x =
            numberToVector(r, dimension, q);

        for (int c = 0; c < factors; ++c) {

            OA[r][c] =
                dotProduct(
                    x,
                    directions[c],
                    field
                );
        }
    }

    return OA;
}

// ============================================================
// Direct product of two Orthogonal Arrays
// ============================================================
//
// OA1 has p1 levels.
// OA2 has p2 levels.
//
// Combine:
//
//      (a, b) -> a * p2 + b
//
// giving p1*p2 levels.
//
// ============================================================

vector<vector<int>> directProduct(
    const vector<vector<int>>& A,
    int levelsA,

    const vector<vector<int>>& B,
    int levelsB
) {
    if (A.empty() || B.empty())
        return {};

    int factors = A[0].size();

    if ((int)B[0].size() != factors) {
        throw runtime_error(
            "Arrays have different numbers of factors."
        );
    }

    ll totalRows =
        1LL * A.size() * B.size();

    if (totalRows > 10000000LL) {
        throw runtime_error(
            "Resulting orthogonal array is too large."
        );
    }

    vector<vector<int>> result;

    result.reserve(totalRows);

    for (const auto& rowA : A) {

        for (const auto& rowB : B) {

            vector<int> row(factors);

            for (int c = 0; c < factors; ++c) {

                row[c] =
                    rowA[c] * levelsB
                    + rowB[c];
            }

            result.push_back(move(row));
        }
    }

    return result;
}

// ============================================================
// General OA generator
// ============================================================

vector<vector<int>> generateOrthogonalArray(
    int factors,
    int levels
) {
    if (factors < 2)
        throw invalid_argument(
            "Number of factors must be >= 2."
        );

    if (levels < 2)
        throw invalid_argument(
            "Number of levels must be >= 2."
        );

    // Factor number of levels into prime powers.
    //
    // Example:
    //
    //      6  -> 2 * 3
    //      12 -> 4 * 3
    //      20 -> 4 * 5
    //
    vector<int> components =
        primePowerFactors(levels);

    vector<vector<int>> result;

    int currentLevels = 1;

    bool first = true;

    for (int q : components) {

        vector<vector<int>> componentOA =
            generatePrimePowerOA(
                factors,
                q
            );

        if (first) {

            result = move(componentOA);

            currentLevels = q;

            first = false;

        } else {

            result =
                directProduct(
                    result,
                    currentLevels,
                    componentOA,
                    q
                );

            currentLevels *= q;
        }
    }

    // Internally levels are 0 ... p-1.
    //
    // Convert them to:
    //
    //      1 ... p
    //
    // which is more natural for software testing.

    for (auto& row : result) {
        for (int& value : row) {
            value++;
        }
    }

    return result;
}

// ============================================================
// Verify pairwise orthogonality
// ============================================================

bool verifyOA(
    const vector<vector<int>>& OA,
    int levels
) {
    if (OA.empty())
        return false;

    int rows = OA.size();
    int factors = OA[0].size();

    if (rows % (levels * levels) != 0)
        return false;

    int lambda =
        rows / (levels * levels);

    for (int c1 = 0; c1 < factors; ++c1) {

        for (int c2 = c1 + 1;
             c2 < factors;
             ++c2) {

            vector<vector<int>> count(
                levels,
                vector<int>(levels, 0)
            );

            for (const auto& row : OA) {

                int a = row[c1] - 1;
                int b = row[c2] - 1;

                if (a < 0 || a >= levels ||
                    b < 0 || b >= levels) {
                    return false;
                }

                count[a][b]++;
            }

            for (int a = 0; a < levels; ++a) {

                for (int b = 0;
                     b < levels;
                     ++b) {

                    if (count[a][b] != lambda)
                        return false;
                }
            }
        }
    }

    return true;
}

// ============================================================
// Print
// ============================================================

void printOA(
    const vector<vector<int>>& OA,
    int levels
) {
    int rows = OA.size();
    int factors = OA[0].size();

    cout << "\n========================================\n";
    cout << "       ORTHOGONAL ARRAY GENERATED\n";
    cout << "========================================\n\n";

    cout << "Factors    : " << factors << '\n';
    cout << "Levels     : " << levels << '\n';
    cout << "Test cases : " << rows << '\n';

    cout << "Strength   : 2 (pairwise)\n";

    cout << "Lambda     : "
         << rows / (levels * levels)
         << "\n\n";

    cout << "Test\t";

    for (int c = 0; c < factors; ++c) {
        cout << "F" << c + 1 << '\t';
    }

    cout << '\n';

    for (int r = 0; r < rows; ++r) {

        cout << r + 1 << '\t';

        for (int value : OA[r]) {
            cout << value << '\t';
        }

        cout << '\n';
    }
}

// ============================================================
// main
// ============================================================

int main() {

    int factors;
    int levels;

    cout << "Orthogonal Array Test Generator\n";
    cout << "-------------------------------\n";

    cout << "Enter number of factors: ";
    cin >> factors;

    cout << "Enter number of levels per factor: ";
    cin >> levels;

    try {

        vector<vector<int>> OA =
            generateOrthogonalArray(
                factors,
                levels
            );

        printOA(OA, levels);

        cout << "\nVerifying pairwise orthogonality...\n";

        if (verifyOA(OA, levels)) {
            cout << "Verification PASSED.\n";
            cout << "The generated array is pairwise orthogonal.\n";
        } else {
            cout << "Verification FAILED.\n";
        }

    } catch (const exception& e) {

        cerr << "\nError: "
             << e.what()
             << '\n';

        return 1;
    }

    return 0;
}