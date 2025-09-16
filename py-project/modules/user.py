# user.py
import hashlib
import json
import os
import random
import string
from enum import Enum
from typing import List, Optional

class UserType(Enum):
    STUDENT = "student"
    PROFESSOR = "professor"
    REVIEWER = "reviewer"  
    GUEST_REVIEWER = "guest_reviewer"

class User:
    _students_file = "data/students.json"
    _professors_file = "data/professors.json"
    _guest_reviewers_file = "data/guest_reviewers.json"
    
    def __init__(self, user_id: str, name: str, password: str, user_type: UserType, 
                 national_id: str = None, major: str = None):
        self.user_id = user_id
        self.name = name
        self.password = self._hash_password(password)
        self.user_type = user_type
        self.national_id = national_id
        self.major = major

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        return self.password == hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self) -> dict:
        data = {
            "user_id": self.user_id,
            "name": self.name,
            "password": self.password,
            "user_type": self.user_type.value,
            "national_id": self.national_id
        }
        if self.major:
            data["major"] = self.major
        return data

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            password="",
            user_type=UserType(data["user_type"]),
            national_id=data.get("national_id"),
            major=data.get("major")
        )

    @classmethod
    def _get_file_path(cls, user_type: UserType) -> str:
        if user_type == UserType.STUDENT:
            return cls._students_file
        elif user_type == UserType.PROFESSOR:
            return cls._professors_file
        elif user_type == UserType.GUEST_REVIEWER:
            return "data/guest_reviewers.json" 
        else:
            return ""

    @classmethod
    def _load_users(cls, user_type: UserType) -> List[dict]:
        file_path = cls._get_file_path(user_type)
        if not file_path:
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @classmethod
    def _save_users(cls, users: List[dict], user_type: UserType):
        file_path = cls._get_file_path(user_type)
        if not file_path:
            return
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

    @classmethod
    def login(cls, user_id: str, password: str) -> Optional[tuple]:
        """Login user and return (user_type, user_id) or None if failed"""
        # چک کردن همه انواع کاربران
        for user_type in [UserType.STUDENT, UserType.PROFESSOR, UserType.GUEST_REVIEWER]:
            users = cls._load_users(user_type)
            for user_data in users:
                if user_data["user_id"] == user_id:
                    if hashlib.sha256(password.encode()).hexdigest() == user_data["password"]:
                        return user_type, user_id
        return None

    @classmethod
    def register(cls, user_id: str, name: str, password: str, user_type: UserType, 
                national_id: str = None, major: str = None) -> bool:
        """Register new user"""
        if cls._user_exists(user_id):
            return False
    
        if user_type == UserType.PROFESSOR:
            major = None
    
        if national_id and cls._national_id_exists(national_id, user_type):
            return False
    
        new_user = cls(user_id, name, password, user_type, national_id, major)
        users = cls._load_users(user_type)
        users.append(new_user.to_dict())
        cls._save_users(users, user_type)
        return True
    
    @classmethod
    def reset_password_with_national_id(cls, user_type: UserType, national_id: str) -> Optional[str]:
        """Password recovery with national ID"""
        users = cls._load_users(user_type)
        
        for user_data in users:
            if user_data.get("national_id") == national_id:
                temp_password = cls._generate_temp_password()
                user_data["password"] = hashlib.sha256(temp_password.encode()).hexdigest()
                cls._save_users(users, user_type)
                return temp_password
        
        return None

    @classmethod
    def change_password(cls, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        for user_type in [UserType.STUDENT, UserType.PROFESSOR, UserType.GUEST_REVIEWER]:
            users = cls._load_users(user_type)
            for user_data in users:
                if user_data["user_id"] == user_id:
                    if hashlib.sha256(old_password.encode()).hexdigest() == user_data["password"]:
                        user_data["password"] = hashlib.sha256(new_password.encode()).hexdigest()
                        cls._save_users(users, user_type)
                        return True
        return False

    @classmethod
    def _generate_temp_password(cls, length: int = 8) -> str:
        """Generate temporary password"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    @classmethod
    def _user_exists(cls, user_id: str) -> bool:
        """Check if user ID exists"""
        for user_type in [UserType.STUDENT, UserType.PROFESSOR, UserType.GUEST_REVIEWER]:  # GUEST_REVIEWER اضافه شد
            users = cls._load_users(user_type)
            if any(user["user_id"] == user_id for user in users):
                return True
        return False

    @classmethod
    def _national_id_exists(cls, national_id: str, user_type: UserType) -> bool:
        """Check if national ID exists"""
        users = cls._load_users(user_type)
        return any(user.get("national_id") == national_id for user in users)

    @classmethod
    def redirect_after_login(cls, user_type: UserType, user_id: str):
        """Redirect after login based on user type"""
        try:
            if user_type == UserType.STUDENT:
                from student import StudentSystem
                student_system = StudentSystem(user_id)
                student_system.run()
                
            elif user_type == UserType.PROFESSOR:
                from professor import ProfessorSystem
                professor_system = ProfessorSystem(user_id)
                professor_system.run()
                
            elif user_type in [UserType.REVIEWER, UserType.GUEST_REVIEWER]:
                from reviewer import ReviewerSystem
                reviewer_system = ReviewerSystem(user_id, user_type)
                reviewer_system.run()
                
        except ImportError as e:
            print(f"❌ Error: {e}")
            print("Please make sure all system files exist")

    @classmethod
    def register_reviewer(cls, user_id: str, name: str, password: str,
                         is_guest: bool = False, national_id: str = None, 
                         affiliation: str = None) -> bool:
        """Register new reviewer"""
        if cls._user_exists(user_id):
            return False

        if is_guest:
            user_type = UserType.GUEST_REVIEWER
            new_user = cls(user_id, name, password, user_type, national_id)
            users = cls._load_users(UserType.GUEST_REVIEWER)  # تغییر شد: از GUEST_REVIEWER استفاده کن
            user_data = new_user.to_dict()
            user_data["affiliation"] = affiliation
            users.append(user_data)
            cls._save_users(users, UserType.GUEST_REVIEWER) 
        else:
            # ثبت داور داخلی (همون استاد)
            user_type = UserType.PROFESSOR
            new_user = cls(user_id, name, password, user_type, national_id)
            users = cls._load_users(user_type)
            users.append(new_user.to_dict())
            cls._save_users(users, user_type)
    
        return True

    @classmethod
    def _load_reviewers(cls, user_type: UserType):
        """Load reviewers from file"""
        if user_type == UserType.REVIEWER:
            return cls._load_users(UserType.PROFESSOR)
        else:
            return cls._load_users(UserType.GUEST_REVIEWER)

    @classmethod
    def _save_reviewers(cls, users: List[dict], user_type: UserType):
        """Save reviewers to file"""
        if user_type == UserType.REVIEWER:
            cls._save_users(users, UserType.PROFESSOR)
        else:
            cls._save_users(users, UserType.GUEST_REVIEWER)