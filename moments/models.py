from datetime import datetime, timezone
from typing import Optional

from flask import current_app
from flask_avatars import Identicon
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, String, Text, event, func, select, engine
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from moments.core.extensions import db, whooshee


role_permission = db.Table(
    'role_permission',
    Column('role_id', ForeignKey('role.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', ForeignKey('permission.id', ondelete='CASCADE'), primary_key=True),
)


class Permission(db.Model):
    __tablename__ = 'permission'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)

    roles: Mapped[list['Role']] = relationship(
        secondary=role_permission,
        back_populates='permissions',
        passive_deletes=True
    )

    def __repr__(self):
        return f'Permission {self.id}: {self.name}'


class Role(db.Model):
    __tablename__ = 'role'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)

    users: WriteOnlyMapped['User'] = relationship(back_populates='role', passive_deletes=True)
    permissions: Mapped[list['Permission']] = relationship(
        secondary=role_permission,
        back_populates='roles',
        passive_deletes=True
    )

    @staticmethod
    def init_role():
        permissions_by_role  = {
            'Locked': ['FOLLOW', 'COLLECT'],
            'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'],
            'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE'],
            'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE', 'ADMIN'],
        }

        for role_name in permissions_by_role:
            role = db.session.scalar(select(Role).filter_by(name=role_name))
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions = []
            for permission_name in permissions_by_role[role_name]:
                permission = db.session.scalar(select(Permission).filter_by(name=permission_name))
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
        db.session.commit()

    def __repr__(self):
        return f'Role {self.id}: {self.name}'


class Follow(db.Model):
    __tablename__ = 'follow'

    follower_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    followed_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    follower: Mapped['User'] = relationship(foreign_keys=[follower_id], back_populates='following', lazy='joined')
    followed: Mapped['User'] = relationship(foreign_keys=[followed_id], back_populates='followers', lazy='joined')

    def __repr__(self):
        return f'Follow: follower_id={self.follower_id}, followed_id={self.followed_id}'


class Collection(db.Model):
    __tablename__ = 'collection'

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey('photo.id', ondelete='CASCADE'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped['User'] = relationship(back_populates='collections', lazy='joined')
    photo: Mapped['Photo'] = relationship(back_populates='collections', lazy='joined')

    def __repr__(self):
        return f'Collect: user_id={self.user_id}, photo_id={self.photo_id}'


@whooshee.register_model('name', 'username')
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(30))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(String(120))
    location: Mapped[Optional[str]] = mapped_column(String(50))
    member_since: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    avatar_s: Mapped[Optional[str]] = mapped_column(String(64))
    avatar_m: Mapped[Optional[str]] = mapped_column(String(64))
    avatar_l: Mapped[Optional[str]] = mapped_column(String(64))
    avatar_raw: Mapped[Optional[str]] = mapped_column(String(64))
    confirmed: Mapped[bool] = mapped_column(default=False)
    locked: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)
    public_collections: Mapped[bool] = mapped_column(default=True)
    receive_comment_notification: Mapped[bool] = mapped_column(default=True)
    receive_follow_notification: Mapped[bool] = mapped_column(default=True)
    receive_collect_notification: Mapped[bool] = mapped_column(default=True)

    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey('role.id'))

    role: Mapped['Role'] = relationship(back_populates='users')
    photos: WriteOnlyMapped['Photo'] = relationship(back_populates='author', cascade='all, delete-orphan', passive_deletes=True)
    comments: WriteOnlyMapped['Comment'] = relationship(
        back_populates='author', cascade='all, delete-orphan', passive_deletes=True
    )
    notifications: WriteOnlyMapped['Notification'] = relationship(
        back_populates='receiver', cascade='all, delete-orphan', passive_deletes=True
    )
    collections: WriteOnlyMapped['Collection'] = relationship(
        back_populates='user', cascade='all, delete-orphan', passive_deletes=True
    )
    following: WriteOnlyMapped['Follow'] = relationship(
        foreign_keys=[Follow.follower_id], back_populates='follower', cascade='all, delete-orphan', passive_deletes=True
    )
    followers: WriteOnlyMapped['Follow'] = relationship(
        foreign_keys=[Follow.followed_id], back_populates='followed', cascade='all, delete-orphan', passive_deletes=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.generate_avatar()
        self.follow(self)  # follow self
        self.set_role()

    @property
    def password(self):
        raise AttributeError('Write-only property!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def set_role(self):
        admin_email = current_app.config['MOMENTS_ADMIN_EMAIL']
        if self.role is None:
            role_name = 'Administrator' if self.email == admin_email else 'User'
            self.role = db.session.scalar(select(Role).filter_by(name=role_name))
            db.session.commit()

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user):
        follow = db.session.scalar(self.following.select().filter_by(followed_id=user.id))
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        if user.id is None:  # user.id will be None when follow self
            return False
        follow = db.session.scalar(self.following.select().filter_by(followed_id=user.id))
        return follow is not None

    def is_followed_by(self, user):
        follow = db.session.scalar(self.followers.select().filter_by(follower_id=user.id))
        return follow is not None

    def collect(self, photo):
        if not self.is_collecting(photo):
            collection = Collection(user=self, photo=photo)
            db.session.add(collection)
            db.session.commit()

    def uncollect(self, photo):
        collection = db.session.scalar(self.collections.select().filter_by(photo_id=photo.id))
        if collection:
            db.session.delete(collection)
            db.session.commit()

    def is_collecting(self, photo):
        collection = db.session.scalar(self.collections.select().filter_by(photo_id=photo.id))
        return collection is not None

    def lock(self):
        self.locked = True
        locked_role = db.session.scalar(select(Role).filter_by(name='Locked'))
        self.role = locked_role
        db.session.commit()

    def unlock(self):
        self.locked = False
        user_role = db.session.scalar(select(Role).filter_by(name='User'))
        self.role = user_role
        db.session.commit()

    def block(self):
        self.active = False
        db.session.commit()

    def unblock(self):
        self.active = True
        db.session.commit()

    def generate_avatar(self):
        avatar = Identicon()
        self.avatar_s, self.avatar_m, self.avatar_l = avatar.generate(text=self.username)
        db.session.commit()

    @property
    def is_admin(self):
        return self.role.name == 'Administrator'

    @property
    def is_active(self):
        return self.active

    def can(self, permission_name):
        permission = db.session.scalar(select(Permission).filter_by(name=permission_name))
        return permission is not None and self.role is not None and permission in self.role.permissions

    @property
    def followers_count(self):
        stmt = self.followers.select().with_only_columns(func.count())
        return db.session.scalar(stmt) - 1  # minus user self

    @property
    def following_count(self):
        stmt = self.following.select().with_only_columns(func.count())
        return db.session.scalar(stmt) - 1  # minus user self

    @property
    def photos_count(self):
        return db.session.scalar(select(func.count(Photo.id)).filter_by(author_id=self.id))

    @property
    def collections_count(self):
        return db.session.scalar(select(func.count(Collection.user_id)).filter_by(photo_id=self.id))

    @property
    def notifications_count(self):
        return db.session.scalar(select(func.count(Notification.id)).filter_by(receiver_id=self.id, is_read=False))

    def __repr__(self):
        return f'User {self.id}: {self.username}'


photo_tag = db.Table(
    'photo_tag',
    Column('photo_id', ForeignKey('photo.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True),
)


@whooshee.register_model('description')
class Photo(db.Model):
    __tablename__ = 'photo'

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(64))
    filename_s: Mapped[str] = mapped_column(String(64))
    filename_m: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)
    can_comment: Mapped[bool] = mapped_column(default=True)
    flag: Mapped[int] = mapped_column(default=0)

    author_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'))

    author: Mapped['User'] = relationship(back_populates='photos')
    comments: WriteOnlyMapped['Comment'] = relationship(
        back_populates='photo', cascade='all, delete-orphan', passive_deletes=True
    )
    collections: WriteOnlyMapped['Collection'] = relationship(
        back_populates='photo', cascade='all, delete-orphan', passive_deletes=True
    )
    tags: Mapped[list['Tag']] = relationship(secondary=photo_tag, back_populates='photos', passive_deletes=True)

    @property
    def collectors_count(self):
        return db.session.scalar(select(func.count(Collection.user_id)).filter_by(photo_id=self.id))

    @property
    def comments_count(self):
        return db.session.scalar(select(func.count(Comment.id)).filter_by(photo_id=self.id))

    def __repr__(self):
        return f'Photo {self.id}: {self.filename}'


@whooshee.register_model('name')
class Tag(db.Model):
    __tablename__ = 'tag'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True, unique=True)

    photos: WriteOnlyMapped['Photo'] = relationship(secondary=photo_tag, back_populates='tags', passive_deletes=True)

    @property
    def photos_count(self):
        return db.session.scalar(select(func.count(photo_tag.c.photo_id)).filter_by(tag_id=self.id))

    def __repr__(self):
        return f'Tag {self.id}: {self.name}'


class Comment(db.Model):
    __tablename__ = 'comment'

    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)
    flag: Mapped[int] = mapped_column(default=0)

    replied_id: Mapped[Optional[int]] = mapped_column(ForeignKey('comment.id', ondelete='CASCADE'))
    author_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'))
    photo_id: Mapped[int] = mapped_column(ForeignKey('photo.id', ondelete='CASCADE'))

    photo: Mapped['Photo'] = relationship(back_populates='comments')
    author: Mapped['User'] = relationship(back_populates='comments')
    replies: WriteOnlyMapped['Comment'] = relationship(
        back_populates='replied', cascade='all, delete-orphan', passive_deletes=True
    )
    replied: Mapped['Comment'] = relationship(back_populates='replies', remote_side=[id])

    def __repr__(self):
        return f'Comment {self.id}: {self.body}'


class Notification(db.Model):
    __tablename__ = 'notification'

    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)

    receiver_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'))

    receiver: Mapped['User'] = relationship(back_populates='notifications')

    def __repr__(self):
        return f'Notification {self.id}: {self.message}'


# enbale foreign key support for SQLite
@event.listens_for(engine.Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    import sqlite3

    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


@event.listens_for(User, 'after_delete', named=True)
def delete_avatars(**kwargs):
    target = kwargs['target']
    for filename in [target.avatar_s, target.avatar_m, target.avatar_l, target.avatar_raw]:
        if filename is not None:  # avatar_raw may be None
            path = current_app.config['AVATARS_SAVE_PATH'] / filename
            if path.exists():  # not every filename map a unique file
                path.unlink()


@event.listens_for(Photo, 'after_delete', named=True)
def delete_photos(**kwargs):
    target = kwargs['target']
    for filename in [target.filename, target.filename_s, target.filename_m]:
        path = current_app.config['MOMENTS_UPLOAD_PATH'] / filename
        if path.exists():  # not every filename map a unique file
            path.unlink()
