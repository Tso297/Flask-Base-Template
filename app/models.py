from app import db
from flask_marshmallow import Marshmallow
from datetime import datetime, timezone


class User(db.Model):
        id = db.Column(db.Integer, primary_key= True)
        displayName = db.Column(db.String(45), nullable=False, unique=True)
        uid = db.Column(db.String(100), nullable=False, unique=True)
        email = db.Column(db.String(100), nullable=False)
        carts = db.relationship('Carts', backref='user', lazy=True)

        def __init__(self, displayName, uid, email):
            self.displayName = displayName
            self.uid = uid
            self.email = email

class Carts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custom_blend = db.Column(db.String(10000), nullable=False)
    totalPrice = db.Column(db.Float(precision=2), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    user_id = db.Column(db.String(100), db.ForeignKey('user.uid'), nullable=False)

    def __init__(self, custom_blend, totalPrice, user_id):
        self.custom_blend = custom_blend
        self.totalPrice = totalPrice
        self.user_id = user_id

class Orders(db.Model):
      id = db.Column(db.Integer, primary_key= True)
      order = db.Column(db.String(10000), nullable = False)
      totalPrice = db.Column(db.Float(precision=2), nullable=False)
      createdAt = db.Column(db.DateTime, default = datetime.now(timezone.utc))
    
      def __init__(self, order, totalPrice):
          self.order = order
          self.totalPrice = totalPrice

class UserSchema(Marshmallow().Schema):
    class Meta:
        fields = ['displayName', 'uid', 'email']

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class CartSchema(Marshmallow().Schema):
    class Meta:
        fields = ['id', 'custom_blend', 'totalPrice', 'user_id']

cart_schema = CartSchema()
carts_schema = CartSchema(many=True)

class OrderSchema(Marshmallow().Schema):
    class Meta:
        fields = ['id', 'custom_blend', 'totalPrice']

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)