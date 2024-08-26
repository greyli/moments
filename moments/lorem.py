import os
import random

from faker import Faker
from flask import current_app
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from moments.core.extensions import db
from moments.models import Comment, Notification, Photo, Tag, User

fake = Faker()


def fake_admin():
    admin = User(
        name='Grey Li',
        username='greyli',
        password='moments',
        email='admin@helloflask.com',
        bio=fake.sentence(),
        website='https://greyli.com',
        confirmed=True,
    )
    notification = Notification(message='Hello, welcome to Moments.', receiver=admin)
    db.session.add(notification)
    db.session.add(admin)
    db.session.commit()


def fake_user(count=10):
    for _ in range(count):
        user = User(
            name=fake.name(),
            confirmed=True,
            username=fake.user_name(),
            password='123456',
            bio=fake.sentence(),
            location=fake.city(),
            website=fake.url(),
            member_since=fake.date_this_decade(),
            email=fake.email(),
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_follow(count=30):
    for _ in range(count):
        user = db.session.scalar(select(User).order_by(func.random()).limit(1))
        user2 = db.session.scalar(select(User).order_by(func.random()).limit(1))
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
        r = lambda: random.randint(128, 255)  # noqa: E731
        img = Image.new(mode='RGB', size=(800, 800), color=(r(), r(), r()))
        img.save(upload_path / filename)

        user_count = db.session.scalar(select(func.count(User.id)))
        user = db.session.get(User, random.randint(1, user_count))
        photo = Photo(
            description=fake.text(),
            filename=filename,
            filename_m=filename,
            filename_s=filename,
            author=user,
            created_at=fake.date_time_this_year(),
        )
        db.session.add(photo)

        # tags
        for _ in range(random.randint(1, 5)):
            tag_count = db.session.scalar(select(func.count(Tag.id)))
            tag = db.session.get(Tag, random.randint(1, tag_count))
            if tag not in photo.tags:
                photo.tags.append(tag)
    db.session.commit()


def fake_collect(count=50):
    for _ in range(count):
        user_count = db.session.scalar(select(func.count(User.id)))
        user = db.session.get(User, random.randint(1, user_count))
        photo_count = db.session.scalar(select(func.count(Photo.id)))
        photo = db.session.get(Photo, random.randint(1, photo_count))
        user.collect(photo)
    db.session.commit()


def fake_comment(count=100):
    for _ in range(count):
        user_count = db.session.scalar(select(func.count(User.id)))
        user = db.session.get(User, random.randint(1, user_count))
        photo_count = db.session.scalar(select(func.count(Photo.id)))
        photo = db.session.get(Photo, random.randint(1, photo_count))
        comment = Comment(author=user, body=fake.sentence(), created_at=fake.date_time_this_year(), photo=photo)
        db.session.add(comment)
    db.session.commit()
