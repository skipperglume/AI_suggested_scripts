#line 1 "/home/lofu/Documents/working_dir/shell_scripts/cext/sum_c/sum.cpp"
extern "C" // required when using C++ compiler
long long mysum(int n, int* array) {
    // return type is 64 bit integer
    long long res = 0;
    for (int i = 0; i < n; ++i) {
        res += array[i];
    }
    return res;
}
