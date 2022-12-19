#line 1 "/home/lofu/Documents/working_dir/shell_scripts/cext/sum_sub/add_and_subtract.cpp"


// Function to add two integer numbers and subtract a third one
int add_and_subtract(int a, int b, int c)
{
    // Return the result
    return a + b - c;
}
// g++ -fPIC -shared add_and_subtract.cpp -o libadd_and_subtract.so