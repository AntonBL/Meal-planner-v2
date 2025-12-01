#!/usr/bin/env python3
"""
Setup script for generating secure authentication configuration.

This script creates a .streamlit/config.yaml file with:
- A randomly generated secret key for session cookies
- Your chosen username, email, and hashed password
"""

import getpass
import secrets
from pathlib import Path

import bcrypt
import yaml


def generate_secret_key() -> str:
    """Generate a cryptographically secure random key."""
    return secrets.token_hex(32)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def main():
    print("=" * 60)
    print("AI Recipe Planner - Authentication Setup")
    print("=" * 60)
    print()

    # Check if config already exists
    config_path = Path(".streamlit/config.yaml")
    if config_path.exists():
        response = input("⚠️  Config file already exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print("Setup cancelled.")
            return

    print("This will create a secure authentication configuration.")
    print()

    # Get user input
    username = input("Enter username: ").strip()
    while not username:
        print("❌ Username cannot be empty!")
        username = input("Enter username: ").strip()

    name = input("Enter your full name: ").strip()
    email = input("Enter your email: ").strip()

    # Get password (hidden input)
    while True:
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            print("❌ Passwords don't match! Try again.")
            continue

        if len(password) < 8:
            print("❌ Password must be at least 8 characters!")
            continue

        break

    print()
    print("🔐 Generating secure configuration...")

    # Generate config
    config = {
        'cookie': {
            'expiry_days': 30,
            'key': generate_secret_key(),
            'name': 'meal_planner_auth'
        },
        'credentials': {
            'usernames': {
                username: {
                    'email': email,
                    'name': name,
                    'password': hash_password(password)
                }
            }
        },
        'preauthorized': {
            'emails': []
        }
    }

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config file
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print()
    print("✅ Configuration created successfully!")
    print(f"📁 Location: {config_path}")
    print()
    print("⚠️  IMPORTANT: Never commit this file to version control!")
    print("   It's already listed in .gitignore")
    print()
    print("🚀 You can now run: streamlit run app.py")
    print()


if __name__ == "__main__":
    main()
