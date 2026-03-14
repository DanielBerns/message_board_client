from cryptography.fernet import Fernet

with open("secure_key.txt", "w") as text:
    text.write(Fernet.generate_key().decode())
