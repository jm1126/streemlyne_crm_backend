from werkzeug.security import generate_password_hash

users = [
    ("ateeb@forklift.academy", "Ateeb@fai"),
    ("shuja@forklift.academy", "Shuja@fai"),
    ("zaki@forklift.academy", "Zaki@fai"),
]

print("=== Password Hashes ===\n")
for email, password in users:
    hash = generate_password_hash(password, method='pbkdf2:sha256')
    name = email.split('@')[0].title()
    print(f"-- {name}")
    print(f"{hash}\n")