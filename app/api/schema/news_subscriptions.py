from app.api.helpers.utilities import dasherize
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Relationship, Schema


# Create logical data abstraction
class NewsSubscriptionSchema(Schema):
    class Meta:
        type_ = 'news-subscription'
        self_view = 'v1.news_subscription_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.news_subscriptions_list'
        inflect = dasherize
        strict = True
        ordered = True

    id = fields.Str(dump_only=True)
    subscribed = fields.Boolean(required=True)
    subscribed_on_date_time = fields.DateTime(dump_only=True)

    user = Relationship(
        attribute='user',
        self_view='v1.news_subscription_user',
        self_view_kwargs={'id': '<id>'},
        related_view='v1.user_details',
        related_view_kwargs={'id': '<user_id>'},
        schema='UserSchema',
        type_='user',
    )

    news = Relationship(
        attribute='news',
        self_view='v1.news_subscription_news',
        self_view_kwargs={'id': '<news.id>'},
        related_view='v1.news_details',
        related_view_kwargs={'id': '<news.id>'},
        schema='NewsSchema',
        type_='news',
        required=True
    )
