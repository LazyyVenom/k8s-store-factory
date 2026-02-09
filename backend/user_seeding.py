"""
User Seeding Script
Creates sample users with different quota levels for testing
"""

from models import db, User

def seed_users(app):
    """
    Seed the database with sample users
    This function is safe to run multiple times - it won't create duplicates
    """
    with app.app_context():
        # Check if users already exist
        existing_count = User.query.count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} users. Skipping seed.")
            return

        print("🌱 Seeding users...")

        users_to_create = [
            # Admin user - highest quotas
            {
                'username': 'admin',
                'password': 'admin123',
                'max_stores': 6,
                'max_storage_gi': 12,
                'description': 'Administrator account with full access'
            },

            # Demo user - limited access
            {
                'username': 'demo_user',
                'password': 'demo123',
                'max_stores': 3,
                'max_storage_gi': 5,
                'description': 'Demo account for testing'
            },
            # Starter tier
            {
                'username': 'starter',
                'password': 'start123',
                'max_stores': 2,
                'max_storage_gi': 5,
                'description': 'Starter tier - minimal quotas'
            },
        ]

        created_users = []
        for user_data in users_to_create:
            user = User(
                username=user_data['username'],
                max_stores=user_data['max_stores'],
                max_storage_gi=user_data['max_storage_gi']
            )
            user.set_password(user_data['password'])
            created_users.append(user)

            print(f"  ✓ Creating user: {user_data['username']} "
                  f"(Stores: {user_data['max_stores']}, "
                  f"Storage: {user_data['max_storage_gi']}Gi)")

        db.session.add_all(created_users)
        db.session.commit()

        print(f"✅ Successfully created {len(created_users)} users!")
        print("\n📋 User Credentials Summary:")
        print("=" * 60)
        for user_data in users_to_create:
            print(f"Username: {user_data['username']:15} | "
                  f"Password: {user_data['password']:15} | "
                  f"Stores: {user_data['max_stores']:2} | "
                  f"Storage: {user_data['max_storage_gi']:3}Gi")
        print("=" * 60)


def clear_users(app):
    """
    Clear all users from the database
    WARNING: This will delete all users and their associated stores!
    """
    with app.app_context():
        user_count = User.query.count()
        if user_count == 0:
            print("No users to clear.")
            return

        confirmation = input(f"⚠️  This will delete {user_count} users and ALL their stores. Type 'yes' to confirm: ")
        if confirmation.lower() != 'yes':
            print("Cancelled.")
            return

        User.query.delete()
        db.session.commit()
        print(f"✅ Deleted {user_count} users.")


def list_users(app):
    """
    List all users in the database
    """
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found in database.")
            return

        print("\n📋 Users in Database:")
        print("=" * 70)
        print(f"{'ID':<5} {'Username':<15} {'Max Stores':<12} {'Max Storage':<12} {'Store Count':<12}")
        print("=" * 70)

        for user in users:
            store_count = len(user.stores)
            print(f"{user.id:<5} {user.username:<15} {user.max_stores:<12} "
                  f"{user.max_storage_gi:<12} {store_count:<12}")

        print("=" * 70)
        print(f"Total users: {len(users)}")


# CLI interface
if __name__ == '__main__':
    import sys
    import os

    # Add the current directory to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from flask import Flask
    from models import db, bcrypt

    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store_factory.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python user_seeding.py seed   - Create seed users")
        print("  python user_seeding.py list   - List all users")
        print("  python user_seeding.py clear  - Clear all users (with confirmation)")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'seed':
        seed_users(app)
    elif command == 'list':
        list_users(app)
    elif command == 'clear':
        clear_users(app)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
