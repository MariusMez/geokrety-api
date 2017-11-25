from app.api.bootstrap import api
from app.api.helpers.db import safe_query
from app.api.helpers.permission_manager import has_access
from app.api.schema.geokrety import GeokretSchema, GeokretSchemaPublic
from app.models import db
from app.models.geokret import Geokret
from flask_jwt import current_identity
from flask_rest_jsonapi import (ResourceDetail, ResourceList,
                                ResourceRelationship)


class GeokretList(ResourceList):

    def before_marshmallow(self, args, kwargs):
        if current_identity:
            # Is admin?
            if has_access('is_admin', user_id=current_identity.id):
                self.schema = GeokretSchema

    def post(self, *args, **kwargs):
        self.schema = GeokretSchema
        return super(GeokretList, self).post(args, kwargs)

    current_identity = current_identity
    schema = GeokretSchemaPublic
    decorators = (
        api.has_permission('auth_required', methods="POST"),
    )
    data_layer = {
        'session': db.session,
        'model': Geokret
    }


class GeokretDetail(ResourceDetail):

    def before_marshmallow(self, args, kwargs):
        if current_identity:
            # Is admin?
            if has_access('is_admin', user_id=current_identity.id):
                self.schema = GeokretSchema

            # Is GeoKret owner?
            if kwargs.get('id') is not None:
                geokret = safe_query(self, Geokret, 'id', kwargs['id'], 'geokret_id')
                if geokret.owner_id == current_identity.id:
                    self.schema = GeokretSchema

    # def before_patch(self, args, kwargs, data):
    #     self.schema = GeokretSchema

    current_identity = current_identity
    decorators = (
        api.has_permission('is_owner', methods="PATCH,DELETE",
                           fetch="id", fetch_as="geokret_id",
                           model=Geokret, fetch_key_url="id"),
    )
    methods = ('GET', 'PATCH', 'DELETE')
    schema = GeokretSchemaPublic
    data_layer = {'session': db.session,
                  'model': Geokret,
                  # 'methods': {
                  #     'before_get_object': before_get_object,
                  # },
                  }
#
#
# class UserRelationship(ResourceRelationship):
#     methods = ['GET']
#     schema = UserSchema
#     data_layer = {'session': db.session,
#                   'model': User}