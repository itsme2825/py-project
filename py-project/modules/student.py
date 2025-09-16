# student.py
from user import User, UserType
import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from werkzeug.utils import secure_filename
import os

class RequestStatus(Enum):
    PENDING = "Pending Approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class DefenseStatus(Enum):
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class StudentSystem(User):
    _thesis_requests_file = "data/thesis_requests.json"
    _defense_requests_file = "data/defense_requests.json"
    _courses_file = "data/courses.json"
    
    def __init__(self, user_id: str):
        users = self._load_users(UserType.STUDENT)
        user_data = next((user for user in users if user["user_id"] == user_id), None)
        
        if user_data:
            super().__init__(
                user_id=user_data["user_id"],
                name=user_data["name"],
                password="",
                user_type=UserType.STUDENT,
                national_id=user_data.get("national_id"),
                major=user_data.get("major")
            )
            print(f"🎓 Student System initialized for: {self.name}")
        else:
            raise ValueError(f"Student with ID {user_id} not found")
    
    def run(self):
        print("\n" + "="*50)
        print(f"👨‍🎓 WELCOME {self.name.upper()}")
        print("="*50)
        
        while True:
            print("\n1. Request Thesis Course")
            print("2. View Thesis Request Status")
            print("3. Request Defense")
            print("4. View Defense Request Status")
            print("5. View My Defense Grade")
            print("6. Change Password")
            print("7. Logout")
            
            choice = input("\nSelect option: ")
            
            if choice == "1":
                self.request_thesis_course()
            elif choice == "2":
                self.view_thesis_status()
            elif choice == "3":
                self.request_defense()
            elif choice == "4":
                self.view_defense_status()
            elif choice == "5":
                self.view_my_grade()
            elif choice == "6":
                self.change_password_menu()
            elif choice == "7":
                print("👋 Logging out...")
                break
            else:
                print("❌ Invalid selection")
    
    def request_thesis_course(self):
        print("\n📝 Available Thesis Courses:")
    
        courses = self._load_courses()
        available_courses = [c for c in courses if c.get("capacity",0) > 0 
                             and c.get("major","").lower() == (self.major or "").lower()]
    
        if not available_courses:
            print("❌ No available courses for your major")
            return
    
        existing_requests = self._load_thesis_requests()
        student_requests = [r for r in existing_requests if r.get("student_id") == self.user_id]
    
        if any(r.get("status") == RequestStatus.PENDING.value for r in student_requests):
            print("❌ You already have a pending request")
            return
    
        if any(r.get("status") == RequestStatus.APPROVED.value for r in student_requests):
            print("✅ You already have an approved thesis course")
            return
    
        rejected_requests = [r for r in student_requests if r.get("status") == RequestStatus.REJECTED.value]
        if rejected_requests:
            print("⚠️ Your previous request was rejected. You can submit a new request.")
    
        for i, course in enumerate(available_courses, 1):
            print(f"{i}. {course.get('title')} - Professor: {course.get('professor')} - Capacity: {course.get('capacity')}")

        try:
            choice = int(input("\nSelect course number: ")) - 1
            if 0 <= choice < len(available_courses):
                selected_course = available_courses[choice]
                thesis_request = {
                    "request_id": f"TR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "student_id": self.user_id,
                    "student_name": self.name,
                    "course_id": selected_course.get("course_id"),
                    "course_title": selected_course.get("title"),
                    "professor": selected_course.get("professor"),
                    "request_date": datetime.now().isoformat(),
                    "status": RequestStatus.PENDING.value,
                    "major": self.major
                }
            
                existing_requests.append(thesis_request)
                self._save_thesis_requests(existing_requests)
            
                for course in courses:
                    if course.get("course_id") == selected_course.get("course_id"):
                        course["capacity"] = course.get("capacity",0) - 1
                        break
                self._save_courses(courses)
            
                print("✅ Thesis request submitted successfully!")
        except ValueError:
            print("❌ Please enter a valid number")

    def request_defense(self):
        print("\n🎓 Thesis Defense Request")
    
        thesis_requests = self._load_thesis_requests()
        approved_thesis = next((t for t in thesis_requests 
                            if t.get("student_id") == self.user_id 
                            and t.get("status") == RequestStatus.APPROVED.value), None)
    
        if not approved_thesis:
            print("❌ You need an approved thesis course first")
            return
    
        approval_date = datetime.fromisoformat(approved_thesis.get("approval_date", datetime.now().isoformat()))
        if datetime.now() < approval_date + timedelta(minutes=3):
            print("❌ You need to wait 3 minutes after thesis approval")
            return
    
        defense_requests = self._load_defense_requests()
        existing_defenses = [d for d in defense_requests if d.get("student_id") == self.user_id]
    
        if any(d.get("status") in [DefenseStatus.UNDER_REVIEW.value, DefenseStatus.APPROVED.value] for d in existing_defenses):
            print("❌ You already have a defense request in process")
            return
    
        rejected_defenses = [d for d in existing_defenses if d.get("status") == DefenseStatus.REJECTED.value]
        if rejected_defenses:
            print("⚠️ Your previous defense request was rejected. You can submit a new request.")
    
        print("\nPlease provide defense information:")
        thesis_title = input("Thesis Title: ")
        abstract = input("Abstract: ")
        keywords = input("Keywords (comma-separated): ")

        print("\n📁 File Upload:")
        pdf_path = self._upload_file("thesis_pdf")
        first_page_path = self._upload_file("first_page_image")

        if not pdf_path or not first_page_path:
            print("❌ File upload failed")
            return
    
        defense_request = {
            "defense_id": f"DR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "student_id": self.user_id,
            "student_name": self.name,
            "thesis_title": thesis_title,
            "abstract": abstract,
            "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
            "pdf_path": pdf_path,
            "first_page_path": first_page_path,
            "request_date": datetime.now().isoformat(),
            "status": DefenseStatus.UNDER_REVIEW.value,
            "professor": approved_thesis.get("professor"),
            "professor_id": approved_thesis.get("professor_id"),
            "course_id": approved_thesis.get("course_id")
        }
    
        defense_requests.append(defense_request)
        self._save_defense_requests(defense_requests)
    
        print("✅ Defense request submitted successfully!")

    def view_thesis_status(self):
        print("\n📊 Thesis Request Status:")
        
        thesis_requests = self._load_thesis_requests()
        student_requests = [r for r in thesis_requests if r.get("student_id") == self.user_id]
        
        if not student_requests:
            print("❌ No thesis requests found")
            return
        
        for request in student_requests:
            print(f"\nRequest ID: {request.get('request_id')}")
            print(f"Course: {request.get('course_title')}")
            print(f"Professor: {request.get('professor')}")
            print(f"Status: {request.get('status')}")
            print(f"Request Date: {request.get('request_date')}")

    def view_defense_status(self):
        print("\n📊 Defense Request Status:")
        
        defense_requests = self._load_defense_requests()
        student_requests = [r for r in defense_requests if r.get("student_id") == self.user_id]
        
        if not student_requests:
            print("❌ No defense requests found")
            return
        
        for request in student_requests:
            print(f"\nDefense ID: {request.get('defense_id')}")
            print(f"Thesis Title: {request.get('thesis_title')}")
            print(f"Status: {request.get('status')}")
            print(f"Request Date: {request.get('request_date')}")
            if request.get("defense_date"):
                print(f"Defense Date: {request.get('defense_date')} - Location: {request.get('defense_location','-')}")

    def view_my_grade(self):
        """Show the grade assigned to the student (if any)"""
        print("\n📌 My Defense Grade")
        defense_requests = self._load_defense_requests()
        my_defenses = [d for d in defense_requests if d.get("student_id") == self.user_id and d.get("status") == DefenseStatus.APPROVED.value]
        
        if not my_defenses:
            print("❌ No approved defense found or not graded yet")
            return
        
        for d in my_defenses:
            print(f"\nDefense ID: {d.get('defense_id')}")
            print(f"Thesis: {d.get('thesis_title')}")
            grades = d.get("grades", {})
            if not grades:
                print("⏰ No grades submitted yet")
                continue

            # نمایش تمامی نمرات دریافتی از داوران
            for reviewer_id, info in grades.items():
                print(f"\nReviewer: {info.get('reviewer_name','-')} ({reviewer_id})")
                print(f"Type: {info.get('reviewer_type','-')}")
                print(f"Grade: {info.get('label','-')}")
                if info.get('comments'):
                    print(f"Comments: {info.get('comments')}")
                print(f"Grading Date: {info.get('grading_date','-')}")

    def change_password_menu(self):
        print("\n🔄 Change Password")
        old_password = input("Current password: ")
        new_password = input("New password: ")
        
        success = User.change_password(self.user_id, old_password, new_password)
        print("✅ Password changed successfully!" if success else "❌ Password change failed")

    # File management methods
    def _load_thesis_requests(self):
        try:
            with open(self._thesis_requests_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_thesis_requests(self, requests):
        os.makedirs(os.path.dirname(self._thesis_requests_file), exist_ok=True)
        with open(self._thesis_requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)

    def _load_defense_requests(self):
        try:
            with open(self._defense_requests_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_defense_requests(self, requests):
        os.makedirs(os.path.dirname(self._defense_requests_file), exist_ok=True)
        with open(self._defense_requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)

    def _load_courses(self):
        try:
            with open(self._courses_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("❌ courses.json file not found or invalid format")
            print("Please create a courses.json file in data folder")
            return []
    
    def _save_courses(self, courses):
        os.makedirs(os.path.dirname(self._courses_file), exist_ok=True)
        with open(self._courses_file, 'w', encoding='utf-8') as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)

    def _upload_file(self, file_type: str, max_attempts: int = 3) -> str:
        attempt = 0

        while attempt < max_attempts:
            try:
                print(f"\n📁 Upload {file_type} (Attempt {attempt + 1}/{max_attempts})")
                file_path = input(f"Enter path to {file_type} file (or 'cancel' to skip): ")

                if file_path.lower() == 'cancel':
                    print("🚫 File upload cancelled")
                    return None
        
                file_path = file_path.strip().strip('"').strip("'").strip('&').strip()
        
                if not os.path.exists(file_path):
                    print("❌ File not found! Please check the path.")
                    attempt += 1
                    continue
        
                file_ext = os.path.splitext(file_path)[1].lower()
            
                if file_type == "thesis_pdf" and file_ext != '.pdf':
                    print("❌ Only PDF files are allowed for thesis!")
                    attempt += 1
                    continue
                elif file_type == "first_page_image" and file_ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                    print("❌ Only PDF, JPG, JPEG, PNG files are allowed for first page!")
                    attempt += 1
                    continue
                    
                upload_dir = Path("uploads/theses")
                upload_dir.mkdir(parents=True, exist_ok=True)
        
                original_filename = os.path.basename(file_path)
                secure_name = secure_filename(original_filename)
                filename_base = secure_name.rsplit('.', 1)[0] if '.' in secure_name else secure_name

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

                destination_path = None
                for counter in range(10):
                    if counter == 0:
                        new_filename = f"{self.user_id}_{filename_base}_{timestamp}{file_ext}"
                    else:
                        new_filename = f"{self.user_id}_{filename_base}_{timestamp}_{counter}{file_ext}"
                
                    current_path = upload_dir / new_filename
                    if not current_path.exists():
                        destination_path = current_path
                        break
            
                if destination_path is None:
                    print("❌ Could not create unique filename")
                    attempt += 1
                    continue
        
                import shutil
                shutil.copy2(file_path, destination_path)
        
                print(f"✅ {file_type} uploaded successfully: {new_filename}")
                return str(destination_path)
        
            except Exception as e:
                print(f"❌ Error uploading file: {e}")
                attempt += 1
                continue

        print(f"❌ Failed to upload {file_type} after {max_attempts} attempts")
        return None

    def student_grade(self):
        """Show the grade assigned to the student (if any)"""
        print("\n📌 My Defense Grade")
        defense_requests = self._load_defense_requests()
        my_defenses = [
            d for d in defense_requests
            if d.get("student_id") == self.user_id
            and d.get("status") == DefenseStatus.APPROVED.value
            ]

        if not my_defenses:
            print("❌ No approved defense found or not graded yet")
            return

        for d in my_defenses:
            print(f"\n🎓 Defense ID: {d.get('defense_id')}")
            print(f"Thesis: {d.get('thesis_title')}")
            grades = d.get("grades", {})

            if not grades:
                print("⏰ No grades submitted yet")
                continue
                
            print("📊 Received Grades:")
            for reviewer_id, info in grades.items():
                reviewer_name = info.get('reviewer_name', 'Unknown')
                reviewer_type = info.get('reviewer_type', '-')
                grade_label = info.get('label', '-')
                comments = info.get('comments', '')
                grading_date = info.get('grading_date', '-')

                print(f"\n👤 Reviewer: {reviewer_name} ({reviewer_type})")
                print(f"Grade: {grade_label}")
                if comments:
                    print(f"Comments: {comments}")
                print(f"Grading Date: {grading_date}")

        print("\n✅ All grades displayed successfully.")
