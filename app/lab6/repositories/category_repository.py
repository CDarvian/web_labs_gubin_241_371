from models import Category


class CategoryRepository:
    def __init__(self, db):
        self.db = db

    def get_all_categories(self):
        return self.db.session.scalars(self.db.select(Category)).all()
