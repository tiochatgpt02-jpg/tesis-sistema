class User:
    def __init__(self, user_id, username, role, email, phone, grade=None):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.email = email
        self.phone = phone
        self.grade = grade

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'email': self.email,
            'phone': self.phone,
            'grade': self.grade,
        }
