#include <bits/stdc++.h>
using namespace std;

int prec(char c)
{
    if (c == '=')
        return 1;
    if (c == '+' || c == '-')
        return 2;
    if (c == '*' || c == '/' || c == '%')
        return 3;
    return 0;
}

int main()
{
    string s;
    cin >> s;

    stack<string> st;
    stack<char> op;

    int temp = 1;

    for (int i = 0; i < s.size(); i++)
    {
        if (isalpha(s[i]))
        {
            st.push(string(1, s[i]));
        }
        else if (s[i] == '(')
        {
            op.push(s[i]);
        }
        else if (s[i] == ')')
        {
            while (!op.empty() && op.top() != '(')
            {
                string b = st.top();
                st.pop();
                string a = st.top();
                st.pop();
                char o = op.top();
                op.pop();

                string t = "t" + to_string(temp++);
                cout << t << "=" << a << o << b << endl;
                st.push(t);
            }
            op.pop();
        }
        else
        {
            while (!op.empty() && prec(op.top()) >= prec(s[i]))
            {
                string b = st.top();
                st.pop();
                string a = st.top();
                st.pop();
                char o = op.top();
                op.pop();

                string t = "t" + to_string(temp++);
                cout << t << "=" << a << o << b << endl;
                st.push(t);
            }
            op.push(s[i]);
        }
    }

    while (!op.empty())
    {
        string b = st.top();
        st.pop();
        string a = st.top();
        st.pop();
        char o = op.top();
        op.pop();

        string t = "t" + to_string(temp++);
        cout << t << "=" << a << o << b << endl;
        st.push(t);
    }

    return 0;
}