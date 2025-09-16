# main.py
from user import User, UserType
import os
import json
from reviewer import ReviewerSystem

def initialize_data_files():
    """Create necessary data files if they don't exist"""
    os.makedirs("data", exist_ok=True)
    
    # ایجاد فایل guest_reviewers.json اگر وجود ندارد
    guest_reviewers_file = "data/guest_reviewers.json"
    if not os.path.exists(guest_reviewers_file):
        with open(guest_reviewers_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
    # ایجاد فایل‌های دیگر اگر نیاز باشد
    files_to_create = [
        "data/students.json",
        "data/professors.json", 
        "data/thesis_requests.json",
        "data/defense_requests.json",
        "data/courses.json"
    ]
    
    for file_path in files_to_create:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

def show_main_menu():
    print("\n🎓 Thesis Management System")
    print("=" * 40)
    print("1. Student/Professor Login")
    print("2. Reviewer Login")
    print("3. Register Student/Professor")
    print("4. Register Guest Reviewer")
    print("5. Password Recovery")
    print("6. Exit")

def student_professor_login():
    print("\n🔐 Student/Professor Login")
    print("User type:")
    print("1. Student")
    print("2. Professor")
    user_type_choice = input("Select (1/2): ")
    
    if user_type_choice == "1":
        user_type = UserType.STUDENT
    elif user_type_choice == "2":
        user_type = UserType.PROFESSOR
    else:
        print("❌ Invalid selection")
        return
    
    user_id = input("User ID: ")
    password = input("Password: ")
    
    result = User.login(user_id, password)
    
    if result:
        user_type, user_id = result
        print(f"\n✅ Login successful!")
        User.redirect_after_login(user_type, user_id)
    else:
        print("❌ Invalid user ID or password")

def reviewer_login():
    """ورود جداگانه برای داوران"""
    print("\n👨‍⚖️ Reviewer Login")
    print("Reviewer type:")
    print("1. Internal Reviewer ")
    print("2. Guest Reviewer ")
    reviewer_type_choice = input("Select (1/2): ")
    
    if reviewer_type_choice == "1":
        user_type = UserType.REVIEWER
    elif reviewer_type_choice == "2":
        user_type = UserType.GUEST_REVIEWER
    else:
        print("❌ Invalid selection")
        return
    
    user_id = input("Reviewer ID: ")
    password = input("Password: ")
    
    result = User.login(user_id, password)
    
    if result:
        user_type, user_id = result
        print(f"\n✅ Login successful!")
        User.redirect_after_login(user_type, user_id)
    else:
        print("❌ Invalid reviewer ID or password")

def register():
    print("\n📝 Register New User")
    
    print("User type:")
    print("1. Student")
    print("2. Professor")
    user_type_choice = input("Select (1/2): ")
    
    if user_type_choice == "1":
        user_type = UserType.STUDENT
    elif user_type_choice == "2":
        user_type = UserType.PROFESSOR
    else:
        print("❌ Invalid selection")
        return
    
    user_id = input("User ID: ")
    name = input("Full Name: ")
    password = input("Password: ")
    national_id = input("National ID: ")
    major = input("Major: ")  
    
    success = User.register(user_id, name, password, user_type, national_id, major)
    print("✅ Registration successful!" if success else "❌ Registration failed - User ID or National ID already exists")

def password_recovery():
    print("\n🔓 Password Recovery")
    
    print("User type:")
    print("1. Student")
    print("2. Professor")
    user_type_choice = input("Select (1/2): ")
    
    if user_type_choice == "1":
        user_type = UserType.STUDENT
    elif user_type_choice == "2":
        user_type = UserType.PROFESSOR
    else:
        print("❌ Invalid selection")
        return
    
    national_id = input("National ID: ")
    
    temp_password = User.reset_password_with_national_id(user_type, national_id)
    
    if temp_password:
        print(f"🔑 Your temporary password: {temp_password}")
        print("⚠️ Please change your password immediately after login")
    else:
        print("❌ No user found with this National ID")

def register_guest_reviewer():
    """Register new guest reviewer"""
    print("\n📝 Register Guest Reviewer")
    
    user_id = input("Reviewer ID: ")
    name = input("Full Name: ")
    password = input("Password: ")
    national_id = input("National ID: ")
    affiliation = input("Affiliation/Organization: ")
    
    success = User.register_reviewer(
        user_id=user_id,
        name=name,
        password=password,
        is_guest=True,
        national_id=national_id,
        affiliation=affiliation
    )
    
    print("✅ Guest reviewer registered successfully!" if success else "❌ Registration failed - User ID already exists")

def main():
    initialize_data_files()
    
    while True:
        show_main_menu()
        choice = input("\nSelect an option (1-6): ")
        
        if choice == "1":
            student_professor_login()
        elif choice == "2":
            reviewer_login()
        elif choice == "3":
            register()
        elif choice == "4":
            register_guest_reviewer()
        elif choice == "5":
            password_recovery()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()