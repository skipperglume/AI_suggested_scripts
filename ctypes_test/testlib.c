#include <stdio.h>
using namespace std;
void myprint(void);

void myprint()
{
    printf("hello world\n");
}


// gcc -shared -Wl,-soname,testlib -o testlib.so -fPIC testlib.c