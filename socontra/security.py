# Security functions.

import secrets
import string
from cryptography.fernet import Fernet
import base64

letters = string.ascii_letters
digits = string.digits
alphabet = letters + digits

# TODO - make dynamic for each client or agent.
fernet = Fernet(b"_NC755LPWhnD5jk8qHhH4HsNJZ32D6a-yGT3qx2rOMs=")

# Generate random and secure passwords or security tokens.
def generate_password(password_length):
    pwd = ''
    for i in range(password_length):
        pwd += ''.join(secrets.choice(alphabet))
    return pwd

# Encrypt password to store in the database and be decoded when needed. 
# We convert to a string so it can be json serializable.
def encrypt_password(password):
    encrypted_password_byte = fernet.encrypt(password.encode())
    encrypted_password_str = str(base64.b64encode(encrypted_password_byte), 'utf8')
    return encrypted_password_str

# Decrypt the password extracted from the database.
# Convert it back to a byte from a string to do the decoding.
def decrypt_password(encrypted_password_str):
    # Have to do the check for list and tuple below because of the way it can be returned from the database.
    if type(encrypted_password_str) == list or type(encrypted_password_str) == tuple:
        encrypted_password_byte = base64.b64decode(bytes(encrypted_password_str[0], 'utf8'))
    else:
        encrypted_password_byte = base64.b64decode(bytes(encrypted_password_str, 'utf8'))
    return fernet.decrypt(encrypted_password_byte).decode()
