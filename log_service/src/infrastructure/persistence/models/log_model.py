from mongoengine import Document, StringField, DateTimeField, IntField
from datetime import datetime

class LogModel(Document):
    service = StringField(required=True)
    level = StringField(required=True)
    message = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'logs',
        'indexes': [
            'timestamp',
            'service',
            'level'
        ]
    }