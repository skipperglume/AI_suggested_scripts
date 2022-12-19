#line 1 "/home/lofu/Documents/working_dir/shell_scripts/ctypes_test/testlib.c"
#include <stdio.h>
using namespace std;
void myprint(void);

void myprint()
{
    printf("hello world\n");
}


// gcc -shared -Wl,-soname,testlib -o testlib.so -fPIC testlib.c