from services.crypto import encrypt_value, decrypt_value

def test_crypto_roundtrip():
    value = 1234.56
    enc = encrypt_value(value)
    dec = decrypt_value(enc)
    assert abs(dec - value) < 1e-6 