from models import User


class UserRepository:
    def __init__(self, db):
        self.db = db

    def get_all_users(self):
        return self.db.session.scalars(self.db.select(User)).all()

    def get_user_by_id(self, user_id):
        return self.db.session.get(User, user_id)

    def get_user_by_login(self, login):
        return self.db.session.scalar(self.db.select(User).filter_by(login=login))
