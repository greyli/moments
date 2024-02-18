import os
import random

from PIL import Image
from faker import Faker
from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func

from moments.core.extensions import db
from moments.models import User, Photo, Tag, Comment, Notification

fake = Faker()


def fake_admin():
    admin = User(name='Grey Li',
                 username='greyli',
                 password='helloflask',
                 email='admin@helloflask.com',
                 bio=fake.sentence(),
                 website='http://greyli.com',
                 confirmed=True)
    notification = Notification(message='Hello, welcome to Moments.', receiver=admin)
    db.session.add(notification)
    db.session.add(admin)
    db.session.commit()


def fake_user(count=10):
    for _ in range(count):
        user = User(name=fake.name(),
                    confirmed=True,
                    username=fake.user_name(),
                    password='123456',
                    bio=fake.sentence(),
                    location=fake.city(),
                    website=fake.url(),
                    member_since=fake.date_this_decade(),
                    email=fake.email())
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_follow(count=30):
    for _ in range(count):
        user = db.session.execute(
            select(User).order_by(func.random()).limit(1)
        ).scalar()
        user2 = db.session.execute(
            select(User).order_by(func.random()).limit(1)
        ).scalar()
        user.follow(user2)
    db.session.commit()


def fake_tag(count=20):
    for _ in range(count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            fake_tag(1)


def fake_photo(count=30):
    # photos
    upload_path = current_app.config['MOMENTS_UPLOAD_PATH']
    for i in range(count):
        print(i)

        filename = f'random_{i}.jpg'
        r = lambda: random.randint(128, 255)
        img = Image.new(mode='RGB', size=(800, 800), color=(r(), r(), r()))
        img.save(os.path.join(upload_path, filename))

        user_count = db.session.execute(select(func.count(User.id))).scalars().one()
        user = db.session.get(User, random.randint(1, user_count))
        photo = Photo(
            description=fake.text(),
            filename=filename,
            filename_m=filename,
            filename_s=filename,
            author=user,
            timestamp=fake.date_time_this_year()
        )

        # tags
        for _ in range(random.randint(1, 5)):
            tag_count = db.session.execute(select(func.count(Tag.id))).scalars().one()
            tag = db.session.get(Tag, random.randint(1, tag_count))
            if tag not in photo.tags:
                photo.tags.append(tag)

        db.session.add(photo)
    db.session.commit()


def fake_collect(count=50):
    for _ in range(count):
        user_count = db.session.execute(select(func.count(User.id))).scalars().one()
        user = db.session.get(User, random.randint(1, user_count))
        photo_count = db.session.execute(select(func.count(Photo.id))).scalars().one()
        photo = db.session.get(Photo, random.randint(1, photo_count))
        user.collect(photo)
    db.session.commit()


def fake_comment(count=100):
    for _ in range(count):
        user_count = db.session.execute(select(func.count(User.id))).scalars().one()
        user = db.session.get(User, random.randint(1, user_count))
        photo_count = db.session.execute(select(func.count(Photo.id))).scalars().one()
        photo = db.session.get(Photo, random.randint(1, photo_count))
        comment = Comment(
            author=user,
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            photo=photo
        )
        db.session.add(comment)
    db.session.commit()
