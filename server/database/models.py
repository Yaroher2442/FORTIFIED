import uuid
from datetime import date as d_date
from datetime import time as d_time, datetime
from enum import Enum
from ipaddress import IPv4Address
from typing import List

from tortoise import fields, Model
from tortoise.fields import ReverseRelation
from tortoise.queryset import QuerySet


def string_from_db_date(db_date, iso_date_format=False):
    v = db_date
    if isinstance(db_date, datetime):
        if iso_date_format:
            v = db_date.replace(microsecond=0).astimezone().isoformat()
        else:
            v = db_date.astimezone().strftime("%d.%m.%Y, %H:%M:%S %z")
    elif isinstance(db_date, d_date):
        if iso_date_format:
            v = db_date.isoformat()
        else:
            v = db_date.strftime("%d.%m.%Y")
    elif isinstance(db_date, d_time):
        v = db_date.replace(microsecond=0).isoformat()
    return v


class AbstractBaseModel(Model):
    id = fields.IntField(pk=True)

    async def values_dict(self, m2m_fields: bool = False, fk_fields: bool = False, backward_fk_fields=False,
                          drop_cols: List[str] = None, iso_date_format=True, all_fetched=True, full_info=False) -> dict:
        def _field_in_drop(field: str):
            if not full_info and drop_cols and field in drop_cols:
                return True
            return False

        t_d = {}
        for k, v in self.__dict__.items():
            if _field_in_drop(k):
                continue
            v = string_from_db_date(v, iso_date_format)
            if isinstance(v, IPv4Address):
                v = str(v)
            if isinstance(v, Enum):
                v = v.value
            if isinstance(v, uuid.UUID):
                v = str(v)
            if not k.startswith('_'):
                t_d.update({k: v})
        if fk_fields or all_fetched:
            for field in self._meta.fk_fields:
                if _field_in_drop(field):
                    continue
                model = getattr(self, field)
                if isinstance(model, QuerySet):
                    if not fk_fields and all_fetched:
                        continue
                    model = await model
                if model:
                    t_d.update({field: await model.values_dict()})
        if m2m_fields or all_fetched:
            for field in self._meta.m2m_fields:
                if _field_in_drop(field):
                    continue
                models = getattr(self, field)
                if not models._fetched:
                    if not m2m_fields and all_fetched:
                        continue
                    models = await models
                t_d.update({field: [await i.values_dict() for i in models if i]})
        if backward_fk_fields or all_fetched:
            for field in self._meta.backward_fk_fields:
                if _field_in_drop(field):
                    continue
                model = getattr(self, field)
                if not model._fetched:
                    if not backward_fk_fields and all_fetched:
                        continue
                    print(model)
                    if isinstance(model, ReverseRelation):
                        model = await model.all()
                t_d.update({field: [await i.values_dict() for i in model if i]})
        return t_d

    class Meta:
        abstract = True


class User(AbstractBaseModel):
    email = fields.CharField(max_length=255, unique=True)
    password = fields.TextField()
    salt = fields.TextField()
    last_login = fields.DatetimeField(auto_now=True)
    careate_add = fields.DatetimeField(auto_now_add=True)


class UserTokens(AbstractBaseModel):
    user = fields.ForeignKeyField("app.User")
    access_token = fields.TextField()
    refresh_token = fields.TextField()
    expire_at = fields.DatetimeField()


class Directory(AbstractBaseModel):
    name = fields.TextField()


class Photo(AbstractBaseModel):
    dir = fields.ManyToManyField("app.Directory")
    server_name = fields.UUIDField(default=uuid.uuid4)
    display_name = fields.TextField(null=True)
    from_app = fields.TextField(null=True)
