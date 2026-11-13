class Topic:
    def __init__(self, topic_id, title, description, status, grade):
        self.topic_id = topic_id
        self.title = title
        self.description = description
        self.status = status
        self.grade = grade

    def to_dict(self):
        return {
            'topic_id': self.topic_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'grade': self.grade,
        }
