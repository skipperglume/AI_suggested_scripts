#include <iostream>
using namespace std;

// Function to find the maximum value in the array and its position
// This function uses C++ templates to work with arrays of any type
void Welcome(){
    std::cout<< "Welcome, Aristocrat!\n";
}
// template <typename T>
// pair<T,T> findMax(T arr[], int size)
// {
//     // Initialize variables to store the maximum value and its position
//     T max = arr[0];
//     int pos = 0;

//     // Loop through the array and update the maximum value and its position
//     // if a larger value is found
//     for (int i = 1; i < size; i++)
//     {
//         if (arr[i] > max)
//         {
//             max = arr[i];
//             pos = i;
//         }
//     }

//     // Print the maximum value and its position
//     cout << "The maximum value is " << max << " at position " << pos << endl;
//     return std::make_pair(pos, max);
// }
// template <typename T>
// void vfindMax(T arr[], int size)
// {
//     // Initialize variables to store the maximum value and its position
//     T max = arr[0];
//     int pos = 0;

//     // Loop through the array and update the maximum value and its position
//     // if a larger value is found
//     for (int i = 1; i < size; i++)
//     {
//         if (arr[i] > max)
//         {
//             max = arr[i];
//             pos = i;
//         }
//     }

//     // Print the maximum value and its position
//     cout << "The maximum value is " << max << " at position " << pos << endl;
    
// }

// int main()
// {
//     // Create arrays of different types and call the findMax function
    
//     int arr1[] = { 10, 20, 30, 40, 50 };
//     int size1 = sizeof(arr1) / sizeof(arr1[0]);
//     pair<int, int > int_pair1 = findMax(arr1, size1);
//     vfindMax(arr1, size1);
//     std::cout<< int_pair1.first << " "<<int_pair1.second<<std::endl;

//     double arr2[] = { 1.2, 3.4, 5.6, 7.8, 9.1 };
//     int size2 = sizeof(arr2) / sizeof(arr2[0]);
//     pair<int, float > int_pair2 = findMax(arr2, size2);
//     vfindMax(arr2, size2);
//     std::cout<< int_pair2.first << " "<<int_pair2.second<<std::endl;

//     char arr3[] = { 'a', 'b', 'c', 'd', 'e' };
//     int size3 = sizeof(arr3) / sizeof(arr3[0]);
//     pair<int, char > int_pair3 = findMax(arr3, size3);
//     std::cout<< int_pair3.first << " "<<int_pair3.second<<std::endl;
//     findMax(arr3, size3);

//     return 0;
// }
/*
g++ -o out.o Find_Max_Template.cxx && ./out.o
g++ -shared -fPIC -o findMaxlibcpplib.so Find_Max_Template.cxx
gcc -fPIC -shared -o findMaxlibcpplib.so Find_Max_Template.cxx


gcc -shared -Wl,-soname,Find_Max_Template -o Find_Max_Template.so -fPIC Find_Max_Template.cxx
*/