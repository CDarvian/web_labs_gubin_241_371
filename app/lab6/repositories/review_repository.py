from models import Review


SORT_NEWEST = 'newest'
SORT_POSITIVE = 'positive'
SORT_NEGATIVE = 'negative'

VALID_SORTS = {SORT_NEWEST, SORT_POSITIVE, SORT_NEGATIVE}


class ReviewRepository:
    def __init__(self, db):
        self.db = db

    def _base_query(self, course_id):
        return self.db.select(Review).filter_by(course_id=course_id)

    def _apply_sort(self, query, sort):
        if sort == SORT_POSITIVE:
            return query.order_by(Review.rating.desc(), Review.created_at.desc())
        if sort == SORT_NEGATIVE:
            return query.order_by(Review.rating.asc(), Review.created_at.desc())
        return query.order_by(Review.created_at.desc())

    def get_latest(self, course_id, limit=5):
        query = self._apply_sort(self._base_query(course_id), SORT_NEWEST).limit(limit)
        return self.db.session.scalars(query).all()

    def get_user_review(self, course_id, user_id):
        if user_id is None:
            return None
        return self.db.session.scalar(
            self._base_query(course_id).filter_by(user_id=user_id)
        )

    def get_paginated(self, course_id, sort=SORT_NEWEST, page=1, per_page=10):
        sort = sort if sort in VALID_SORTS else SORT_NEWEST
        query = self._apply_sort(self._base_query(course_id), sort)
        return self.db.paginate(query, page=page, per_page=per_page)

    def add_review(self, course, user_id, rating, text):
        review = Review(
            course_id=course.id,
            user_id=user_id,
            rating=rating,
            text=text,
        )
        course.rating_sum += rating
        course.rating_num += 1
        self.db.session.add(review)
        self.db.session.commit()
        return review
