from hashlib import sha256

for i in range(1, 5000):
    sha256(str(i).encode())