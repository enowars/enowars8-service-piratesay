import ctypes
import re
import socket
import sys
import time

IDENTITY_LENGTH = 64

# Load the C standard library
libc = ctypes.CDLL(None)

# Set argument and return types for rand_r
libc.rand_r.argtypes = [ctypes.POINTER(ctypes.c_uint)]
libc.rand_r.restype = ctypes.c_int

# Set argument and return types for rand and srand
libc.rand.argtypes = []
libc.rand.restype = ctypes.c_int
libc.srand.argtypes = [ctypes.c_uint]
libc.srand.restype = None

def generate_identity_string_rand():
    identity_string = ''.join(chr(ord('a') + (libc.rand() % 26)) for _ in range(IDENTITY_LENGTH))
    return identity_string

def generate_identity_string_rand_r(state):
    state_ptr = ctypes.c_uint(state)
    identity_string = ''.join(chr(ord('a') + (libc.rand_r(ctypes.byref(state_ptr)) % 26)) for _ in range(IDENTITY_LENGTH))
    return identity_string, state_ptr.value

# Test both functions with the same seed
start_seed = 12345
libc.srand(start_seed)

seed = start_seed
for i in range(10):
    identity_rand = generate_identity_string_rand()
    identity_rand_r, seed = generate_identity_string_rand_r(seed)

    print (f"identity_rand: {identity_rand}")
    print (f"identity_rand_r: {identity_rand_r}")

