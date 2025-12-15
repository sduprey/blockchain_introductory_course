from Pyfhel import Pyfhel

# 1. Create FHE context
HE = Pyfhel()
HE.contextGen(
    scheme='CKKS',     # CKKS supports real numbers
    n=2**14,           # Polynomial modulus degree
    scale=2**30        # Precision scale
)
HE.keyGen()

# 2. Plaintext values
a = 3.5
b = 2.0

# 3. Encrypt values
enc_a = HE.encryptFrac(a)
enc_b = HE.encryptFrac(b)

# 4. Compute on encrypted data
enc_sum = enc_a + enc_b
enc_product = enc_a * enc_b

# 5. Decrypt results
sum_result = HE.decryptFrac(enc_sum)
product_result = HE.decryptFrac(enc_product)

print("Decrypted sum:", sum_result)
print("Decrypted product:", product_result)