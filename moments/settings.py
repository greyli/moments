import os
import sys
from pathlib import Path
from enum import Enum

BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_PREFIX = 'sqlite:///' if sys.platform.startswith('win') else 'sqlite:////'


class Operations(Enum):
    CONFIRM = 'confirm'
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'


class BaseConfig:
    MOMENTS_ADMIN_EMAIL = os.getenv('MOMENTS_ADMIN', 'admin@helloflask.com')
    MOMENTS_ERROR_EMAIL_SUBJECT = '[Greybook] Application Error'
    MOMENTS_LOGGING_PATH = os.getenv('MOMENTS_LOGGING_PATH', BASE_DIR / 'logs/moments.log')
    MOMENTS_PHOTO_PER_PAGE = 12
    MOMENTS_COMMENT_PER_PAGE = 15
    MOMENTS_NOTIFICATION_PER_PAGE = 20
    MOMENTS_USER_PER_PAGE = 20
    MOMENTS_MANAGE_PHOTO_PER_PAGE = 20
    MOMENTS_MANAGE_USER_PER_PAGE = 30
    MOMENTS_MANAGE_TAG_PER_PAGE = 50
    MOMENTS_MANAGE_COMMENT_PER_PAGE = 30
    MOMENTS_SEARCH_RESULT_PER_PAGE = 20
    MOMENTS_MAIL_SUBJECT_PREFIX = '[Moments]'
    MOMENTS_UPLOAD_PATH = os.getenv('MOMENTS_UPLOAD_PATH', BASE_DIR / 'uploads')
    MOMENTS_PHOTO_SIZES = {'small': 400, 'medium': 800}
    MOMENTS_PHOTO_SUFFIXES = {
        MOMENTS_PHOTO_SIZES['small']: '_s',  # thumbnail
        MOMENTS_PHOTO_SIZES['medium']: '_m',  # display
    }

    SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # file size exceed to 3 Mb will return a 413 error response.

    BOOTSTRAP_SERVE_LOCAL = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AVATARS_SAVE_PATH = MOMENTS_UPLOAD_PATH / 'avatars'
    AVATARS_SIZE_TUPLE = (30, 100, 200)

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Moments Admin', MAIL_USERNAME)

    DROPZONE_ALLOWED_FILE_CUSTOM = True
    DROPZONE_ALLOWED_FILE_TYPE = '.png,.jpg,.jpeg'
    DROPZONE_MAX_FILE_SIZE = 3
    DROPZONE_MAX_FILES = 30
    DROPZONE_ENABLE_CSRF = True

    WHOOSHEE_MIN_STRING_LEN = 1
    MOMENTS_SLOW_QUERY_THRESHOLD = 1


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = SQLITE_PREFIX + str(BASE_DIR / 'data-dev.db')
    REDIS_URL = 'redis://localhost'


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'  # in-memory database


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', SQLITE_PREFIX + str(BASE_DIR / 'data.db'))


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
