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
    id = db.Column(db.Integer, primary_key=True)
    order_details = db.Column(db.String(10000), nullable=False)
    totalPrice = db.Column(db.Float(precision=2), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    uid = db.Column(db.String(100), db.ForeignKey('user.uid'), nullable=False)  # Ensuring it references 'uid' in the 'user' table
    shipping_name = db.Column(db.String(255), nullable=False)
    shipping_line1 = db.Column(db.String(255), nullable=False)
    shipping_city = db.Column(db.String(255), nullable=False)
    shipping_country = db.Column(db.String(255), nullable=False)
    shipping_postal_code = db.Column(db.String(255), nullable=False)

    def __init__(self, order_details, totalPrice, uid, shipping_name, shipping_line1, shipping_city, shipping_country, shipping_postal_code):
        self.order_details = order_details
        self.totalPrice = totalPrice
        self.uid = uid
        self.shipping_name = shipping_name
        self.shipping_line1 = shipping_line1
        self.shipping_city = shipping_city
        self.shipping_country = shipping_country
        self.shipping_postal_code = shipping_postal_code
        
class OrderSchema(Marshmallow().Schema):
    class Meta:
        fields = ('id', 'order_details', 'totalPrice', 'createdAt', 'uid', 
                  'shipping_name', 'shipping_line1', 'shipping_city', 
                  'shipping_country', 'shipping_postal_code')

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


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