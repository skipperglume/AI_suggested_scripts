import ctypes

testlib = ctypes.CDLL('/home/lofu/Documents/working_dir/shell_scripts/ctypes_test/testlib.so')
testlib.myprint()