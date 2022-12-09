#include <iostream>
#include <dlfcn.h> // for dlopen, dlsym, dlclose

// Function prototype

typedef int (*add_and_subtract_t)(int, int, int);
int main()
{
    // Open the shared library
    void* handle = dlopen("/home/lofu/Documents/working_dir/shell_scripts/cext/sum_sub/libadd_and_subtract.so", RTLD_LAZY);

    add_and_subtract_t add_and_subtract = (add_and_subtract_t) dlsym(handle, "add_and_subtract");

    // use the function
    int result = add_and_subtract(1, 2, 3);
    std::cout << "Result: " << result << std::endl;

    // close the library
    dlclose(handle);

    return 0;

    // Check if the library was opened successfully
    // if (!handle) {
    //     std::cerr << "Error: could not open shared library: " << dlerror() << std::endl;
    //     return 1;
    // }

    // Load the function from the library
    // void* symbol = dlsym(handle, "add_and_subtract");

    // Check if the function was loaded successfully
    // if (!symbol) {
    //     std::cerr << "Error: could not find function in shared library: " << dlerror() << std::endl;
    //     return 1;
    // }

    // Cast the function pointer to the correct type
    // int (*func)(int, int, int) = reinterpret_cast<int(*)(int, int, int)>(symbol);

    // // Call the function
    // int result = func(10, 20, 5);

    // // Print the result
    // std::cout << "Result: " << result << std::endl;

    // // Close the shared library
    // dlclose(handle);

    // return 0;
}
// g++ -o a.out  -ldl main.cpp
// g++ main.cpp -ldl -o main