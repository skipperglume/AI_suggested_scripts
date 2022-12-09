# Import the ctypes module
import ctypes

# Load the libcpplib.so shared library
# Find_Max_Template = ctypes.cdll.LoadLibrary('/home/lofu/Documents/working_dir/shell_scripts/python_examples/Find_Max_Template.so')
Find_Max_Template = ctypes.CDLL('/home/lofu/Documents/working_dir/shell_scripts/python_examples/Find_Max_Template.so')
                            
# print(Find_Max_Template.__dict__)
# Create an array of integers
arr = [10, 20, 30, 40, 50]

# Call the findMax function from the shared library
Find_Max_Template.Welcome()
# Find_Max_Template.vfindMax(arr, len(arr))
