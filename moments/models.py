import os
from datetime import datetime, timezone
from typing import Optional

from flask import current_app
from flask_avatars import Identicon
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, event, func, select
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from moments.core.extensions import db, whooshee

# relationship table
roles_permissions = Table(
    'roles_permissions',
    db.Model.metadata,
    Column('role_id', Integer, ForeignKey('role.id')),
    Column('permission_id', Integer, ForeignKey('permission.id')),
)


class Permission(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)

    roles: Mapped[list['Role']] = relationship(secondary=roles_permissions, back_populates='permissions')


class Role(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)

    users: WriteOnlyMapped['User'] = relationship(back_populates='role', passive_deletes=True)
    permissions: Mapped[list['Permission']] = relationship(secondary=roles_permissions, back_populates='roles')

    @staticmethod
    def init_role():
        roles_permissions_map = {
            'Locked': ['FOLLOW', 'COLLECT'],
            'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'],
            'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE'],
            'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE', 'ADMINISTER'],
        }

        for role_name in roles_permissions_map:
            role = db.session.scalar(select(Role).filter_by(name=role_name))
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions = []
            for permission_name in roles_permissions_map[role_name]:
                permission = db.session.scalar(select(Permission).filter_by(name=permission_name))
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
        db.session.commit()


# relationship object
class Follow(db.Model):
    follower_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    followed_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    follower: Mapped['User'] = relationship(foreign_keys=[follower_id], back_populates='following', lazy='joined')
    followed: Mapped['User'] = relationship(foreign_keys=[followed_id], back_populates='followers', lazy='joined')


# relationship object
class Collect(db.Model):
    collector_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    collected_id: Mapped[int] = mapped_column(ForeignKey('photo.id'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    collector: Mapped['User'] = relationship(back_populates='collections', lazy='joined')
    collected: Mapped['Photo'] = relationship(back_populates='collectors', lazy='joined')


@whooshee.register_model('name', 'username')
class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(30))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(String(120))
    location: Mapped[Optional[str]] = mapped_column(String(50))
    member_since: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
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
    photos: WriteOnlyMapped[list['Photo']] = relationship(back_populates='author', cascade='all', passive_deletes=True)
    comments: WriteOnlyMapped[list['Comment']] = relationship(
        back_populates='author', cascade='all', passive_deletes=True
    )
    notifications: WriteOnlyMapped[list['Notification']] = relationship(
        back_populates='receiver', cascade='all', passive_deletes=True
    )
    collections: WriteOnlyMapped[list['Collect']] = relationship(
        back_populates='collector', cascade='all', passive_deletes=True
    )
    following: WriteOnlyMapped[list['Follow']] = relationship(
        foreign_keys=[Follow.follower_id], back_populates='follower', cascade='all', passive_deletes=True
    )
    followers: WriteOnlyMapped[list['Follow']] = relationship(
        foreign_keys=[Follow.followed_id], back_populates='followed', cascade='all', passive_deletes=True
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
        if self.role is None:
            role_name = 'Administrator' if self.email == current_app.config['MOMENTS_ADMIN_EMAIL'] else 'User'
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
        follow = db.session.scalar(select(Follow).filter_by(follower_id=self.id, followed_id=user.id))
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        follow = db.session.scalar(select(Follow).filter_by(follower_id=self.id, followed_id=user.id))
        return follow is not None

    def is_followed_by(self, user):
        follow = db.session.scalar(select(Follow).filter_by(follower_id=user.id, followed_id=self.id))
        return follow is not None

    def collect(self, photo):
        if not self.is_collecting(photo):
            collect = Collect(collector=self, collected=photo)
            db.session.add(collect)
            db.session.commit()

    def uncollect(self, photo):
        collect = db.session.scalar(select(Collect).filter_by(collector_id=self.id, collected_id=photo.id))
        if collect:
            db.session.delete(collect)
            db.session.commit()

    def is_collecting(self, photo):
        collect = db.session.scalar(select(Collect).filter_by(collector_id=self.id, collected_id=photo.id))
        return collect is not None

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
        return (
            db.session.scalar(select(func.count(Follow.follower_id)).filter_by(followed_id=self.id)) - 1
        )  # minus user self

    @property
    def following_count(self):
        return (
            db.session.scalar(select(func.count(Follow.followed_id)).filter_by(follower_id=self.id)) - 1
        )  # minus user self

    @property
    def photos_count(self):
        return db.session.scalar(select(func.count(Photo.id)).filter_by(author_id=self.id))

    @property
    def collections_count(self):
        return db.session.scalar(select(func.count(Collect.collector_id)).filter_by(collected_id=self.id))

    @property
    def notifications_count(self):
        return db.session.scalar(select(func.count(Notification.id)).filter_by(receiver_id=self.id, is_read=False))


tagging = Table(
    'tagging',
    db.Model.metadata,
    Column('photo_id', Integer, ForeignKey('photo.id')),
    Column('tag_id', Integer, ForeignKey('tag.id')),
)


@whooshee.register_model('description')
class Photo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(64))
    filename_s: Mapped[str] = mapped_column(String(64))
    filename_m: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc), index=True)
    can_comment: Mapped[bool] = mapped_column(default=True)
    flag: Mapped[int] = mapped_column(default=0)

    author_id: Mapped[int] = mapped_column(ForeignKey('user.id'))

    author: Mapped['User'] = relationship(back_populates='photos')
    comments: WriteOnlyMapped[list['Comment']] = relationship(
        back_populates='photo', cascade='all', passive_deletes=True
    )
    collectors: WriteOnlyMapped[list['Collect']] = relationship(
        back_populates='collected', cascade='all', passive_deletes=True
    )
    tags: Mapped[list['Tag']] = relationship(secondary=tagging, back_populates='photos')

    @property
    def collectors_count(self):
        return db.session.scalar(select(func.count(Collect.collector_id)).filter_by(collected_id=self.id))

    @property
    def comments_count(self):
        return db.session.scalar(select(func.count(Comment.id)).filter_by(photo_id=self.id))


@whooshee.register_model('name')
class Tag(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True, unique=True)

    photos: WriteOnlyMapped['Photo'] = relationship(secondary=tagging, back_populates='tags', passive_deletes=True)

    @property
    def photos_count(self):
        return db.session.scalar(select(func.count(tagging.c.photo_id)).filter_by(tag_id=self.id))


class Comment(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc), index=True)
    flag: Mapped[int] = mapped_column(default=0)

    replied_id: Mapped[Optional[int]] = mapped_column(ForeignKey('comment.id'))
    author_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    photo_id: Mapped[int] = mapped_column(ForeignKey('photo.id'))

    photo: Mapped['Photo'] = relationship(back_populates='comments')
    author: Mapped['User'] = relationship(back_populates='comments')
    replies: WriteOnlyMapped[list['Comment']] = relationship(
        back_populates='replied', cascade='all', passive_deletes=True
    )
    replied: Mapped['Comment'] = relationship(back_populates='replies', remote_side=[id])


class Notification(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc), index=True)

    receiver_id: Mapped[int] = mapped_column(ForeignKey('user.id'))

    receiver: Mapped['User'] = relationship(back_populates='notifications')


@event.listens_for(User, 'after_delete', named=True)
def delete_avatars(**kwargs):
    target = kwargs['target']
    for filename in [target.avatar_s, target.avatar_m, target.avatar_l, target.avatar_raw]:
        if filename is not None:  # avatar_raw may be None
            path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], filename)
            if os.path.exists(path):  # not every filename map a unique file
                os.remove(path)


@event.listens_for(Photo, 'after_delete', named=True)
def delete_photos(**kwargs):
    target = kwargs['target']
    for filename in [target.filename, target.filename_s, target.filename_m]:
        path = os.path.join(current_app.config['MOMENTS_UPLOAD_PATH'], filename)
        if os.path.exists(path):  # not every filename map a unique file
            os.remove(path)
