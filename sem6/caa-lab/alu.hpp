#ifndef ALU_H
#define ALU_H

#include <cstdint>

struct ALUResult
{
    uint8_t value; // result of operation
    bool Z; // zero flag
    bool C; // carry flag
};

/* ================= LOGIC GATES ================= */

inline bool AND(bool a, bool b) { return a & b; }
inline bool OR(bool a, bool b) { return a | b; }
inline bool XOR(bool a, bool b) { return a ^ b; }
inline bool NOT(bool a) { return !a; }

/* ================= ADDERS ================= */

struct HalfAdder
{
    bool sum;
    bool carry;
};

inline HalfAdder half_adder(bool a, bool b)
{
    return {XOR(a, b), AND(a, b)};
}

struct FullAdder
{
    bool sum;
    bool carry;
};

inline FullAdder full_adder(bool a, bool b, bool cin)
{
    HalfAdder h1 = half_adder(a, b);
    HalfAdder h2 = half_adder(h1.sum, cin);
    return {h2.sum, OR(h1.carry, h2.carry)};
}

/* =============== 8-BIT ADDER ================= */

inline uint8_t add8(uint8_t a, uint8_t b, bool &carry_out)
{
    uint8_t r = 0;
    bool carry = 0;

    for (int i = 0; i < 8; i++)
    {
        bool ai = (a >> i) & 1;
        bool bi = (b >> i) & 1;

        FullAdder f = full_adder(ai, bi, carry);

        if (f.sum)
            r |= (1 << i);
        carry = f.carry;
    }

    carry_out = carry;
    return r;
}

/* =============== TWO’S COMPLEMENT ================= */

inline uint8_t twos(uint8_t x)
{
    bool c;
    return add8(~x, 1, c);
}

/* =============== SUBTRACTION ================= */

inline uint8_t sub8(uint8_t a, uint8_t b, bool &borrow)
{
    bool c;
    uint8_t r = add8(a, twos(b), c);
    borrow = NOT(c);
    return r;
}

/* =============== MULTIPLY ================= */

inline uint8_t mul8(uint8_t a, uint8_t b, bool &carry)
{
    uint8_t r = 0;
    carry = 0;

    for (int i = 0; i < 8; i++)
    {
        if ((b >> i) & 1)
        {
            bool c;
            uint8_t shifted = a << i;
            r = add8(r, shifted, c);
            if (c)
                carry = 1;
        }
    }
    return r;
}

/* =============== DIVISION ================= */

inline uint8_t div8(uint8_t a, uint8_t b, bool &div0)
{
    if (b == 0)
    {
        div0 = true;
        return 0;
    }

    div0 = false;
    uint8_t q = 0;
    uint8_t r = a;

    for (int i = 7; i >= 0; i--)
    {
        uint8_t d = b << i;
        bool borrow;
        uint8_t tmp = sub8(r, d, borrow);

        if (!borrow)
        {
            r = tmp;
            q |= (1 << i);
        }
    }

    return q;
}

/* =============== POWER ================= */

inline uint8_t pow8(uint8_t a, uint8_t b, bool &carry)
{
    uint8_t r = 1;
    carry = 0;

    for (int i = 0; i < b; i++)
        r = mul8(r, a, carry);

    return r;
}

/* =============== CPU-VISIBLE ALU ================= */

inline ALUResult alu_add(uint8_t a, uint8_t b)
{
    bool c;
    uint8_t r = add8(a, b, c);
    return {r, r == 0, c};
}

inline ALUResult alu_sub(uint8_t a, uint8_t b)
{
    bool br;
    uint8_t r = sub8(a, b, br);
    return {r, r == 0, br};
}

inline ALUResult alu_mul(uint8_t a, uint8_t b)
{
    bool c;
    uint8_t r = mul8(a, b, c);
    return {r, r == 0, c};
}

inline ALUResult alu_div(uint8_t a, uint8_t b, bool &div0)
{
    uint8_t r = div8(a, b, div0);
    return {r, r == 0, 0};
}

inline ALUResult alu_pow(uint8_t a, uint8_t b)
{
    bool c;
    uint8_t r = pow8(a, b, c);
    return {r, r == 0, c};
}

inline ALUResult alu_cmp(uint8_t a, uint8_t b)
{
    bool br;
    sub8(a, b, br);
    return {0, a == b, br};
}

#endif
