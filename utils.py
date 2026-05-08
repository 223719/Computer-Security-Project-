from Crypto.Cipher import AES
import hashlib
import base64

KEY = b"1234567890123456"

def encrypt(message):
    cipher = AES.new(KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

def decrypt(enc_message):
    raw = base64.b64decode(enc_message)
    nonce = raw[:16]
    tag = raw[16:32]
    ciphertext = raw[32:]
    cipher = AES.new(KEY, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()

def generate_hash(message):
    return hashlib.sha256(message.encode()).hexdigest()

def verify_hash(message, received_hash):
    return generate_hash(message) == received_hash