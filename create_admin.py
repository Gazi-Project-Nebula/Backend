from database import SessionLocal
import crud, schemas

def create_admin():
    db = SessionLocal()
    
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")
    
    # Check if user exists
    user = crud.get_user_by_username(db, username=username)
    
    if user:
        print(f"User {username} already exists. Updating role to 'admin'...")
        user.role = "admin"
        db.commit()
        print("Success! User is now an admin.")
    else:
        print(f"Creating new admin user {username}...")
        # Create user object
        user_data = schemas.UserCreate(
            username=username,
            password=password,
            role="admin" # Explicitly set role
        )
        crud.create_user(db=db, user=user_data)
        print("Success! Admin user created.")
    
    db.close()

if __name__ == "__main__":
    create_admin()