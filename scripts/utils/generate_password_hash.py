"""
Generate password hash for admin user
Run this to get the correct hash and salt for Admin@123456
"""

import hashlib
import secrets

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password with salt using PBKDF2"""
    if not salt:
        salt = secrets.token_hex(32)
    
    # Use PBKDF2 with SHA256
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    ).hex()
    
    return password_hash, salt

# Generate hash for Admin@123456
password = "Admin@123456"
password_hash, salt = hash_password(password)

print("=" * 60)
print("PASSWORD HASH GENERATOR")
print("=" * 60)
print(f"\nPassword: {password}")
print(f"\nSalt:\n{salt}")
print(f"\nPassword Hash:\n{password_hash}")
print("\n" + "=" * 60)
print("\nSQL INSERT Statement:")
print("=" * 60)
print(f"""
INSERT INTO users (
    username, email, password_hash, salt, full_name, role, 
    is_active, is_verified, department, designation,
    last_password_change, created_at, updated_at
) VALUES (
    'admin',
    'admin@delhipolice.gov.in',
    '{password_hash}',
    '{salt}',
    'System Administrator',
    'admin',
    true,
    true,
    'Delhi Police Cyber Cell',
    'System Administrator',
    NOW(),
    NOW(),
    NOW()
);
""")
print("=" * 60)
