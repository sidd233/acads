int x = 5;
int y = 10;

/* multi-line
   comment should be
   ignored completely */

x = x + y;
z = x @2; // @ is invalid
x = x #1; // # is invalid

while (x != 0)
{
    x = x - 1;
}

return x;
