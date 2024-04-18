from app import db
from flask_marshmallow import Marshmallow
from datetime import datetime, timezone
class User(db.Model):
        id = db.Column(db.Integer, primary_key= True)
        username = db.Column(db.String(45), nullable=False, unique=True)
        email = db.Column(db.String(100), nullable=False, unique=True)
        password = db.Column(db.String(40), nullable=False)

        def __init__(self, username, email, password):
            self.username = username
            self.email = email
            self.password = password

class Carts(db.Model):
      id = db.Column(db.Integer, primary_key= True)
      custom_blend = db.Column(db.String(450), nullable = False)
      totalPrice = db.Column(db.Integer, nullable = False)

      def __init__(self, custom_blend, totalPrice):
          self.custom_blend = custom_blend
          self.totalPrice = totalPrice



# class Seasonalities(db.Model):
#       id = db.Column(db.Integer, primary_key= True)
#       user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
#       ingredients = 
#       name = db.Column(db.String(150), nullable = False)
#       quantity = db.Column(db.String(150), nullable = False)
#       totalPrice = (db.Integer, nullable=False)

#       def __init__(self, user_id, item_size, shipping_address, custom_blend):
#           self.user_id = user_id
#           self.item_size = item_size
#           self.shipping_address = shipping_address
#           self.custom_blend = custom_blend


class UserSchema(Marshmallow().Schema):
    class Meta:
        fields = ['id', 'username', 'password']

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class CartSchema(Marshmallow().Schema):
    class Meta:
        fields = ['id', 'custom_blend']

cart_schema = CartSchema()
carts_schema = CartSchema(many=True)