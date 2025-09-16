# professor.py
from user import User, UserType
from student import RequestStatus, DefenseStatus
import json
import os
from datetime import datetime
from typing import List, Dict

class ProfessorSystem(User):
    _thesis_requests_file = "data/thesis_requests.json"
    _defense_requests_file = "data/defense_requests.json"
    _courses_file = "data/courses.json"
    _guest_reviewers_file = "data/guest_reviewers.json"
    _max_guidance_capacity = 5
    _max_review_capacity = 10

    def __init__(self, user_id: str):
        users = self._load_users(UserType.PROFESSOR)
        user_data = next((user for user in users if user["user_id"] == user_id), None)
        
        if user_data:
            super().__init__(
                user_id=user_data["user_id"],
                name=user_data["name"],
                password="",
                user_type=UserType.PROFESSOR,
                national_id=user_data.get("national_id"),
                major=user_data.get("major")
            )
            print(f"👨‍🏫 Professor System initialized for: {self.name}")
        else:
            raise ValueError(f"Professor with ID {user_id} not found")
    
    def run(self):
        print("\n" + "="*50)
        print(f"👨‍🏫 WELCOME PROFESSOR {self.name.upper()}")
        print("="*50)
        
        while True:
            print("\n1. Manage Thesis Requests")
            print("2. Manage Defense Requests")
            print("3. Check Guidance Capacity")
            print("4. Check Review Capacity")
            print("5. Grade Defense Sessions")
            print("6. Change Password")
            print("7. Logout")
            
            choice = input("\nSelect option: ")
            
            if choice == "1":
                self.manage_thesis_requests()
            elif choice == "2":
                self.manage_defense_requests()
            elif choice == "3":
                self.check_guidance_capacity()
            elif choice == "4":
                self.check_review_capacity()
            elif choice == "5":
                self.grade_defense_sessions()
            elif choice == "6":
                self.change_password_menu()
            elif choice == "7":
                print("👋 Logging out...")
                break
            else:
                print("❌ Invalid selection")

    def manage_thesis_requests(self):
        print(f"\n📋 Thesis Requests Management for Professor {self.name}")
        print("=" * 70)
        
        thesis_requests = self._load_thesis_requests()
        pending_requests = [r for r in thesis_requests if r.get("professor") == self.name and r.get("status") == RequestStatus.PENDING.value]
        approved_requests = [r for r in thesis_requests if r.get("professor") == self.name and r.get("status") == RequestStatus.APPROVED.value]
        rejected_requests = [r for r in thesis_requests if r.get("professor") == self.name and r.get("status") == RequestStatus.REJECTED.value]
        
        print(f"📊 Status: {len(pending_requests)} Pending | {len(approved_requests)} Approved | {len(rejected_requests)} Rejected")
        
        if not pending_requests:
            print("❌ No pending thesis requests")
            if approved_requests or rejected_requests:
                print("\n📜 Request History:")
                for req in approved_requests + rejected_requests:
                    status_icon = "✅" if req["status"] == RequestStatus.APPROVED.value else "❌"
                    print(f"   {status_icon} {req['student_name']} - {req['course_title']} - {req['status']}")
            return
        
        for i, request in enumerate(pending_requests, 1):
            print(f"\n{i}. Request ID: {request['request_id']}")
            print(f"   Student: {request['student_name']} ({request['student_id']})")
            print(f"   Course: {request['course_title']}")
            print(f"   Major: {request.get('major','-')}")
            print(f"   Request Date: {request['request_date']}")
        
        try:
            choice = int(input("\nSelect request to manage (0 to cancel): ")) - 1
            if choice == -1:
                return
            if 0 <= choice < len(pending_requests):
                selected_request = pending_requests[choice]
                self._manage_single_thesis_request(selected_request)
        except ValueError:
            print("❌ Please enter a valid number")

    def _manage_single_thesis_request(self, request: Dict):
        print(f"\n📝 Managing Request: {request['request_id']}")
        print(f"Student: {request['student_name']}")
        print(f"Course: {request['course_title']}")
        
        current_guidance_count = self._get_current_guidance_count()
        if current_guidance_count >= self._max_guidance_capacity:
            print("❌ You have reached your maximum guidance capacity (5 students)")
            return
        
        print(f"\nRemaining guidance capacity: {self._max_guidance_capacity - current_guidance_count}/5")
        
        print("\n1. Approve Request")
        print("2. Reject Request")
        print("3. Cancel")
        
        choice = input("\nSelect action: ")
        
        thesis_requests = self._load_thesis_requests()
        
        for req in thesis_requests:
            if req.get("request_id") == request.get("request_id"):
                if choice == "1":
                    req["status"] = RequestStatus.APPROVED.value
                    req["approval_date"] = datetime.now().isoformat()
                    req["professor_id"] = self.user_id
                    print("✅ Thesis request approved!")
                elif choice == "2":
                    req["status"] = RequestStatus.REJECTED.value
                    req["rejection_date"] = datetime.now().isoformat()
                    print("❌ Thesis request rejected!")
                else:
                    print("🚫 Action cancelled")
                    return
                break
        
        self._save_thesis_requests(thesis_requests)

    def manage_defense_requests(self):
        print(f"\n🎓 Defense Requests Management for Professor {self.name}")
        print("=" * 70)
        
        defense_requests = self._load_defense_requests()
        pending_defenses = [r for r in defense_requests if r.get("professor") == self.name and r.get("status") == DefenseStatus.UNDER_REVIEW.value]
        approved_defenses = [r for r in defense_requests if r.get("professor") == self.name and r.get("status") == DefenseStatus.APPROVED.value]
        rejected_defenses = [r for r in defense_requests if r.get("professor") == self.name and r.get("status") == DefenseStatus.REJECTED.value]
        
        print(f"📊 Status: {len(pending_defenses)} Under Review | {len(approved_defenses)} Approved | {len(rejected_defenses)} Rejected")
        
        if not pending_defenses:
            print("❌ No pending defense requests")
            if approved_defenses or rejected_defenses:
                print("\n📜 Defense History:")
                for req in approved_defenses + rejected_defenses:
                    status_icon = "✅" if req["status"] == DefenseStatus.APPROVED.value else "❌"
                    print(f"   {status_icon} {req['student_name']} - {req['thesis_title']} - {req['status']}")
            return
        
        for i, request in enumerate(pending_defenses, 1):
            print(f"\n{i}. Defense ID: {request['defense_id']}")
            print(f"   Student: {request['student_name']} ({request['student_id']})")
            print(f"   Thesis: {request['thesis_title']}")
            print(f"   Request Date: {request['request_date']}")
        
        try:
            choice = int(input("\nSelect defense request to manage (0 to cancel): ")) - 1
            if choice == -1:
                return
            if 0 <= choice < len(pending_defenses):
                selected_request = pending_defenses[choice]
                self._manage_single_defense_request(selected_request)
        except ValueError:
            print("❌ Please enter a valid number")

    def _manage_single_defense_request(self, request: Dict):
        print(f"\n🎓 Managing Defense Request: {request['defense_id']}")
        print(f"Student: {request['student_name']}")
        print(f"Thesis: {request['thesis_title']}")
        print(f"Abstract: {request.get('abstract','')[:100]}...")
        
        print("\n1. Approve Defense Request")
        print("2. Reject Defense Request")
        print("3. View Full Details")
        print("4. Cancel")
        
        choice = input("\nSelect action: ")
        
        defense_requests = self._load_defense_requests()
        
        for req in defense_requests:
            if req.get("defense_id") == request.get("defense_id"):
                if choice == "1":
                    req["status"] = DefenseStatus.APPROVED.value
                    req["approval_date"] = datetime.now().isoformat()
                    req["approved_by"] = self.user_id
                    print("✅ Defense request approved!")
                    print("📅 Now you need to set defense date and select reviewers")
                    self._set_defense_details(req)
                elif choice == "2":
                    req["status"] = DefenseStatus.REJECTED.value
                    req["rejection_date"] = datetime.now().isoformat()
                    req["rejected_by"] = self.user_id
                    rejection_reason = input("Rejection reason: ")
                    req["rejection_reason"] = rejection_reason
                    print("❌ Defense request rejected!")
                elif choice == "3":
                    self._show_defense_details(req)
                    return
                else:
                    print("🚫 Action cancelled")
                    return
                break
        
        self._save_defense_requests(defense_requests)

    def _set_defense_details(self, request: Dict):
        """Set defense date and reviewers with full details"""
        print(f"\n📅 Setting Defense Details for: {request['thesis_title']}")
    
        defense_date = input("Defense date (YYYY-MM-DD HH:MM): ")
        defense_location = input("Defense location: ")

        # انتخاب داور داخلی (از لیست اساتید)
        professors = User._load_users(UserType.PROFESSOR)
        if not professors:
            print("❌ No professors found in the system!")
            return

        print("\n👥 Internal reviewers (اساتید داخلی):")
        for i, prof in enumerate(professors, 1):
            print(f"{i}. {prof['name']} ({prof['user_id']})")

        try:
            internal_choice = int(input("Select internal reviewer number: ")) - 1
            if internal_choice < 0 or internal_choice >= len(professors):
                print("❌ Invalid selection!")
                return
            internal_reviewer = {
                "id": professors[internal_choice]["user_id"],
                "name": professors[internal_choice]["name"]
            }

            request["internal_reviewer_id"] = internal_reviewer["id"]
            request["internal_reviewer"] = internal_reviewer["name"]
        except ValueError:
            print("❌ Please enter a valid number!")
            return

        # انتخاب داور خارجی (از guest_reviewers.json به صورت مستقیم)
        guest_reviewers = []
        try:
            with open(self._guest_reviewers_file, 'r', encoding='utf-8') as gf:
                guest_reviewers = json.load(gf)
        except (FileNotFoundError, json.JSONDecodeError):
            guest_reviewers = []

        if not guest_reviewers:
            print("❌ No guest reviewers available!")
            return

        print("\n🌍 External reviewers:")
        for i, guest in enumerate(guest_reviewers, 1):
            print(f"{i}. {guest.get('name','-')} - {guest.get('affiliation','')} ({guest.get('user_id','-')})")

        try:
            external_choice = int(input("Select external reviewer number: ")) - 1
            if external_choice < 0 or external_choice >= len(guest_reviewers):
                print("❌ Invalid selection!")
                return
            chosen_guest = guest_reviewers[external_choice]
            external_reviewer = {
                "id": chosen_guest.get("user_id"),
                "name": chosen_guest.get("name"),
                "affiliation": chosen_guest.get("affiliation", ""),
                "email": chosen_guest.get("email", "")
            }

            request["external_reviewer_id"] = external_reviewer["id"]
            request["external_reviewer"] = external_reviewer["name"]
        except ValueError:
            print("❌ Please enter a valid number!")
            return

        # ذخیره اطلاعات در درخواست مربوطه
        defense_requests = self._load_defense_requests()
        found = False
        for req in defense_requests:
            if req.get("defense_id") == request.get("defense_id"):
                req.update({
                    "defense_date": defense_date,
                    "defense_location": defense_location,
                    "internal_reviewer": internal_reviewer,
                    "external_reviewer": external_reviewer,
                    "internal_reviewer_id": internal_reviewer["id"],
                    "external_reviewer_id": external_reviewer["id"],
                    "defense_setup_date": datetime.now().isoformat()
                })
                found = True
                break
                
        if not found:
            print("❌ ERROR: Could not find matching defense request!")
            return

        try:
            self._save_defense_requests(defense_requests)
            print("✅ Defense details set successfully!")
        except Exception as e:
            print(f"❌ ERROR saving defense requests: {e}")

    def _show_defense_details(self, request: Dict):
        print(f"\n📋 Defense Request Details:")
        print("=" * 50)
        print(f"Defense ID: {request.get('defense_id')}")
        print(f"Student: {request.get('student_name')} ({request.get('student_id')})")
        print(f"Thesis Title: {request.get('thesis_title')}")
        print(f"Abstract: {request.get('abstract')}")
        print(f"Keywords: {', '.join(request.get('keywords',[]))}")
        print(f"PDF File: {request.get('pdf_path')}")
        print(f"First Page: {request.get('first_page_path')}")
        print(f"Status: {request.get('status')}")
        print(f"Request Date: {request.get('request_date')}")

        if request.get("defense_date"):
            print(f"\n📅 Defense Date: {request.get('defense_date')}")
            print(f"📍 Location: {request.get('defense_location')}")

            internal = request.get("internal_reviewer", {})
            if internal:
                print("\n👤 Internal Reviewer:")
                print(f"   {internal.get('name', 'Not set')} ({internal.get('id', '-')})")
            else:
                print("\n👤 Internal Reviewer: Not set")

            external = request.get("external_reviewer", {})
            if external:
                print("\n🌍 External Reviewer:")
                print(f"   {external.get('name', 'Not set')} ({external.get('id', '-')})")
                if external.get("affiliation"):
                    print(f"   Affiliation: {external['affiliation']}")
                if external.get("email"):
                    print(f"   Email: {external['email']}")
            else:
                print("\n🌍 External Reviewer: Not set")

    def check_guidance_capacity(self):
        current_count = self._get_current_guidance_count()
        remaining = self._max_guidance_capacity - current_count
        
        print(f"\n📊 Guidance Capacity for Professor {self.name}")
        print("=" * 40)
        print(f"Current students: {current_count}")
        print(f"Remaining capacity: {remaining}")
        print(f"Maximum capacity: {self._max_guidance_capacity}")
        
        if current_count >= self._max_guidance_capacity:
            print("❌ You have reached maximum guidance capacity!")
    
    def check_review_capacity(self):
        current_count = self._get_current_review_count()
        remaining = self._max_review_capacity - current_count
        
        print(f"\n📊 Review Capacity for Professor {self.name}")
        print("=" * 40)
        print(f"Current reviews: {current_count}")
        print(f"Remaining capacity: {remaining}")
        print(f"Maximum capacity: {self._max_review_capacity}")
    
    def _get_current_guidance_count(self) -> int:
        thesis_requests = self._load_thesis_requests()
        guided_students = [r for r in thesis_requests 
                          if r.get("professor_id") == self.user_id 
                          and r.get("status") == RequestStatus.APPROVED.value]
        return len(guided_students)
    
    def _get_current_review_count(self) -> int:
        defense_requests = self._load_defense_requests()
        cnt = 0
        for d in defense_requests:
            if (d.get("internal_reviewer_id") == self.user_id) or (d.get("external_reviewer_id") == self.user_id):
                cnt += 1
        return cnt
    
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

    def grade_defense_sessions(self):
        print(f"\n🎯 Grade Defense Sessions - Internal Reviewer {self.name}")
        print("=" * 60)

        defense_requests = self._load_defense_requests()
        my_sessions = []

        for defense in defense_requests:
            if (defense.get("internal_reviewer_id") == self.user_id or 
                (defense.get("internal_reviewer") and 
                 defense["internal_reviewer"].get("id") == self.user_id)):
                my_sessions.append(defense)

        if not my_sessions:
            print("❌ No defense sessions assigned to you as internal reviewer")
            return

        for i, session in enumerate(my_sessions, 1):
            graded = session.get("grades") and self.user_id in session.get("grades", {})
            status = "✅ Graded" if graded else "⏰ Pending Grading"
            print(f"\n{i}. {session.get('thesis_title')}")
            print(f"   Student: {session.get('student_name')}")
            print(f"   Date: {session.get('defense_date', 'Not set')}")
            print(f"   Status: {status}")

        try:
            choice = int(input("\nSelect session to grade (0 to cancel): ")) - 1
            if choice == -1:
                return
            if 0 <= choice < len(my_sessions):
                selected_session = my_sessions[choice]
                self._grade_session(selected_session)
        except ValueError:
            print("❌ Please enter a valid number")
    
    def _grade_session(self, session: Dict):
        print(f"\n📊 Grading: {session.get('thesis_title')}")
        print(f"Student: {session.get('student_name')}")

        if session.get('abstract'):
            print(f"\n📋 Abstract: {session['abstract'][:200]}...")
        if session.get('keywords'):
            print(f"Keywords: {', '.join(session['keywords'])}")

        # انتخاب برچسب نمره
        labels = ["A", "B", "C", "F"]
        print("\nSelect grade label:")
        for i, lab in enumerate(labels, 1):
            print(f"{i}. {lab}")

        while True:
            try:
                idx = int(input("Choose (1-4): ")) - 1
                if 0 <= idx < len(labels):
                    label = labels[idx]
                    break
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Please enter a valid number")

        comments = input("Comments (optional): ")

        defense_requests = self._load_defense_requests()
        for defense in defense_requests:
            if defense.get("defense_id") == session.get("defense_id"):
                if "grades" not in defense:
                    defense["grades"] = {}
                defense["grades"][self.user_id] = {
                    "label": label,
                    "comments": comments,
                    "grading_date": datetime.now().isoformat(),
                    "reviewer_type": "internal",
                    "reviewer_name": self.name
                }
                break

        self._save_defense_requests(defense_requests)
        print("✅ Grade submitted successfully!")

    def view_assigned_reviews(self):
        defense_requests = self._load_defense_requests()

        print(f"\n👀 Your Assigned Defense Reviews - {self.name}")
        print("=" * 50)

        internal_reviews = []
        external_reviews = []

        for defense in defense_requests:
            if (defense.get("internal_reviewer_id") == self.user_id or 
                (defense.get("internal_reviewer") and 
                 defense["internal_reviewer"].get("id") == self.user_id)):
                internal_reviews.append(defense)

            if (defense.get("external_reviewer_id") == self.user_id or 
                (defense.get("external_reviewer") and 
                 defense["external_reviewer"].get("id") == self.user_id)):
                external_reviews.append(defense)

        print(f"\n📋 Internal Reviews: {len(internal_reviews)}")
        for i, review in enumerate(internal_reviews, 1):
            status = "Graded" if review.get("grades") and self.user_id in review.get("grades", {}) else "Pending"
            print(f"{i}. {review.get('thesis_title')} - {review.get('student_name')} - {status}")

        print(f"\n🌍 External Reviews: {len(external_reviews)}")
        for i, review in enumerate(external_reviews, 1):
            status = "Graded" if review.get("grades") and self.user_id in review.get("grades", {}) else "Pending"
            print(f"{i}. {review.get('thesis_title')} - {review.get('student_name')} - {status}")
