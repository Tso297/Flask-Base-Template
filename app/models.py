from app import db
from flask_marshmallow import Marshmallow
from datetime import datetime, timezone
class User(db.Model):
        id = db.Column(db.Integer, primary_key= True)
        username = db.Column(db.String(45), nullable=False, unique=True)
        email = db.Column(db.String(100), nullable=False, unique=True)
        phone_number = db.Column(db.String(20))
        password = db.Column(db.String, nullable=False)

        def __init__(self, username, email, phone_number, password):
            self.username = username
            self.email = email
            self.phone_number = phone_number
            self.password = password

class Orders(db.Model):
      id = db.Column(db.Integer, primary_key= True)
      user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
      item_size = db.Column(db.Integer, nullable=False)
      shipping_address = db.Column(db.String(150), nullable = False)
      custom_blend = db.Column(db.String(150), nullable = False)
      date_created = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

      def __init__(self, user_id, item_size, shipping_address, custom_blend):
          self.user_id = user_id
          self.item_size = item_size
          self.shipping_address = shipping_address
          self.custom_blend = custom_blend


class UserSchema(Marshmallow().Schema):
    class Meta:
        fields = ['id', 'username', 'email', 'phone_number', 'password']

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class OrderSchema(Marshmallow().Schema):
    class Meta:
        fields = ['id', 'item_size', 'shipping_address', 'custom_blend']

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)