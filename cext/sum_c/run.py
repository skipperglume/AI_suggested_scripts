import ctypes
import numpy
import glob

# find the shared library, the path depends on the platform and Python version
libfile = glob.glob('build/lib.linux-x86_64-3.10/sum.cpython-310-x86_64-linux-gnu.so')[0]
print(libfile)

mylib = ctypes.CDLL(libfile)


mylib.mysum.restype = ctypes.c_longlong
mylib.mysum.argtypes = [ctypes.c_int, 
                        numpy.ctypeslib.ndpointer(dtype=numpy.int32)]

array = numpy.arange(0, 100000000, 1, numpy.int32)

# 3. call function mysum
array_sum = mylib.mysum(len(array), array)

print('sum of array: {}'.format(array_sum))
