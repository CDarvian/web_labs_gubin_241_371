import hashlib
import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

from models import Image


class ImageRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, image_id):
        return self.db.session.get(Image, image_id)

    def add_image(self, file):
        img = self._find_by_md5_hash(file)
        if img is not None:
            return img

        file_name = secure_filename(file.filename)
        img = Image(
            id=str(uuid.uuid4()),
            file_name=file_name,
            mime_type=file.mimetype,
            md5_hash=self._md5_hash,
        )
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], img.storage_filename))
        self.db.session.add(img)
        self.db.session.commit()
        return img

    def _find_by_md5_hash(self, file):
        self._md5_hash = hashlib.md5(file.read()).hexdigest()
        file.seek(0)
        return self.db.session.scalar(
            self.db.select(Image).filter(Image.md5_hash == self._md5_hash)
        )
