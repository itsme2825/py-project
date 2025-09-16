# reviewer.py
from user import User, UserType
import json
import os
from datetime import datetime

class ReviewerSystem(User):
    _defense_requests_file = "data/defense_requests.json"
    _guest_reviewers_file = "data/guest_reviewers.json"

    def __init__(self, user_id: str, user_type: UserType):
        self.is_guest = (user_type == UserType.GUEST_REVIEWER)

        if self.is_guest:
            users = self._load_guest_reviewers()
            user_data = next((u for u in users if u.get("user_id") == user_id), None)
            if not user_data:
                raise ValueError("Guest reviewer not found")
            super().__init__(
                user_id=user_data.get("user_id"),
                name=user_data.get("name"),
                password="",
                user_type=UserType.GUEST_REVIEWER
            )
        else:
            # Internal reviewer (از لیست استادها)
            users = self._load_users(UserType.PROFESSOR)
            user_data = next((u for u in users if u.get("user_id") == user_id), None)
            if not user_data:
                raise ValueError("Internal reviewer not found (must be professor)")
            super().__init__(
                user_id=user_data.get("user_id"),
                name=user_data.get("name"),
                password="",
                user_type=UserType.REVIEWER
            )

        print(f"🧾 Reviewer System initialized for: {self.name} (guest={self.is_guest})")

    def run(self):
        while True:
            print("\n1. View Assigned Defense Sessions")
            print("2. Grade a Defense Session")
            print("3. Logout")
            choice = input("Select option: ")
            if choice == "1":
                self.view_assigned_defenses()
            elif choice == "2":
                self.grade_defense_session()
            elif choice == "3":
                break
            else:
                print("❌ Invalid selection")

    # ----------------- فایل‌ها -----------------
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

    def _load_guest_reviewers(self):
        try:
            with open(self._guest_reviewers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    # ----------------- امکانات -----------------
    def view_assigned_defenses(self):
        defenses = self._load_defense_requests()
        assigned = []
        for d in defenses:
            if self.is_guest:
                if d.get("external_reviewer_id") == self.user_id:
                    assigned.append(d)
            else:
                if d.get("internal_reviewer_id") == self.user_id:
                    assigned.append(d)

        print(f"\n📋 Assigned defenses for {self.name} (count={len(assigned)})")
        for i, a in enumerate(assigned,1):
            print(f"\n{i}. {a.get('thesis_title')} - {a.get('student_name')}")
            print(f"   Defense ID: {a.get('defense_id')}")
            print(f"   Date: {a.get('defense_date','Not set')} - Location: {a.get('defense_location','-')}")
            grades = a.get("grades", {})
            status = "Graded" if self.user_id in grades else "Pending"
            print(f"   Status: {status}")

    def grade_defense_session(self):
        defenses = self._load_defense_requests()
        assigned = []
        for d in defenses:
            if self.is_guest:
                if d.get("external_reviewer_id") == self.user_id:
                    assigned.append(d)
            else:
                if d.get("internal_reviewer_id") == self.user_id:
                    assigned.append(d)

        if not assigned:
            print("❌ No assigned defense sessions")
            return

        for i, a in enumerate(assigned,1):
            grades = a.get("grades", {})
            status = "Graded" if self.user_id in grades else "Pending"
            print(f"{i}. {a.get('thesis_title')} - {a.get('student_name')} - {status}")

        try:
            choice = int(input("Select session to grade (0 cancel): ")) - 1
            if choice == -1:
                return
            if not (0 <= choice < len(assigned)):
                print("❌ Invalid selection")
                return
            session = assigned[choice]
        except ValueError:
            print("❌ Please enter a valid number")
            return

        # لیبل‌های نمره
        labels = ["A", "B", "C", "F"]
        print("\nSelect grade label:")
        for i, lab in enumerate(labels,1):
            print(f"{i}. {lab}")
        while True:
            try:
                li = int(input("Choose (1-4): ")) - 1
                if 0 <= li < len(labels):
                    label = labels[li]
                    break
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Invalid input")

        comments = input("Comments (optional): ")

        # ذخیره نمره
        defenses = self._load_defense_requests()
        for d in defenses:
            if d.get("defense_id") == session.get("defense_id"):
                if "grades" not in d:
                    d["grades"] = {}
                d["grades"][self.user_id] = {
                    "label": label,
                    "comments": comments,
                    "grading_date": datetime.now().isoformat(),
                    "reviewer_type": "guest" if self.is_guest else "internal",
                    "reviewer_name": self.name
                }
                break

        self._save_defense_requests(defenses)
        print("✅ Grade saved successfully!")
