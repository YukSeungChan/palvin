# -*- coding:utf-8 -*-
import datetime
import inflect

from sqlalchemy import create_engine, Column, BigInteger, DateTime
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from config import SQLALCHEMY_DATABASE_URI
from utils import (
    camel_case_to_lower_case_underscore,
    OrderedSet
)

exclude_modules = ['palvin', 'models']
inflect_engine = inflect.engine()


class IdMixin(object):
    """
    Provides the :attr:`id` primary key column
    """
    #: Database identity for this model, used for foreign key
    #: references from other models
    id = Column(BigInteger, primary_key=True)

    @classmethod
    def get(cls, _id):
        if any((isinstance(_id, basestring) and _id.isdigit(),
                isinstance(_id, (int, float))),):
            return cls.query.get(int(_id))
        return None


class TimestampMixin(object):
    """
    Provides the :attr:`created_at` and :attr:`updated_at` audit timestamps
    """
    #: Timestamp for when this instance was created, in UTC
    created_at = Column(
        DateTime,
        default=datetime.datetime.now,
        nullable=False
    )
    #: Timestamp for when this instance was last updated (via the app), in UTC
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        nullable=False
    )


class CRUDMixin(object):
    __table_args__ = {'extend_existing': True}

    @classmethod
    def query(cls):
        return db_session.query(cls)

    @classmethod
    def get_by(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_or_create(cls, **kwargs):
        r = cls.get_by(**kwargs)
        if not r:
            r = cls(**kwargs)
            db_session.add(r)
        return r

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)
        return commit and self.save(commit=commit) or self

    def save(self, commit=False):
        db_session.add(self)
        if commit:
            try:
                db_session.commit()
            except Exception:
                db_session.rollback()
                raise
        return self

    def delete(self, commit=True):
        db_session.delete(self)
        return commit and db_session.commit()


class PalvinBase(CRUDMixin, object):

    @declared_attr
    def __tablename__(cls):
        global exclude_modules, inflect_engine

        modules = cls.__module__.split('.')
        modules[-1] = inflect_engine.plural(
            camel_case_to_lower_case_underscore(cls.__name__)
        )
        return '_'.join(
            list(OrderedSet(modules) - OrderedSet(exclude_modules))
        )

    @property
    def repr(self):
        if hasattr(self, 'id') and self.id is not None:
            return '<%s %s>' % (self.__class__.__name__, self.id)
        else:
            return '<%s #>' % self.__class__.__name__

    def __repr__(self):
        return self.repr.encode('utf8')

    def __str__(self):
        return self.repr.encode('utf8')

    def __unicode__(self):
        return self.repr

    def __setattr__(self, key, value):
        return super(PalvinBase, self).__setattr__(key, value)


engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    convert_unicode=True
)

db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine
    )
)

Base = declarative_base(cls=PalvinBase)
Base.query = db_session.query_property()
