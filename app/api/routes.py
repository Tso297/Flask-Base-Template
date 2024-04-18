from app import db
from flask import request, jsonify
from app.models import User, Carts, user_schema, users_schema, cart_schema, carts_schema
from . import api
from datetime import datetime, timezone


###################################################
@api.route('/users', methods = ['POST'])
def create_user():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    user = User(username, email, password)

    db.session.add(user)
    db.session.commit()

    response = user_schema.dump(user)
    return jsonify(response)
###################################################
@api.route('/checkout', methods = ['POST'])
def create_cart():
    custom_blend = []
    for blend in request.json:
        custom_blend.append(blend)

    totalPrice = 0
    for i in range(len(custom_blend)):
        totalPrice += custom_blend[i]["totalPrice"]
        totalPrice = round(totalPrice, 2)

    
    cart = Carts(custom_blend, totalPrice)

    db.session.add(Carts(custom_blend=custom_blend, totalPrice=totalPrice))
    db.session.commit()

    response = cart_schema.dump(cart)
    return jsonify(response)
####################################################
@api.route('/users', methods = ['GET'])
def get_contact():
    users = User.query.all()
    response = users_schema.dump(users)
    return jsonify(response)
####################################################
@api.route('/users/<id>', methods = ['GET'])
def get_single_contact(id):
    user = User.query.get(id)
    response = user_schema.dump(user)
    return jsonify(response)
####################################################
@api.route('/carts', methods = ['GET'])
def get_carts():
    carts = Carts.query.all()
    response = carts_schema.dump(carts)
    return jsonify(response)
####################################################
@api.route('/carts/<id>', methods = ['GET'])
def get_single_cart(id):
    cart = Carts.query.get(id)
    response = cart_schema.dump(cart)
    return jsonify(response)
#####################################################
@api.route('/users/<id>', methods = ['POST', 'PUT'])
def update_user(id):
    user = User.query.get(id)
    user.username = request.json['username']
    user.email = request.json['email']
    user.password = request.json['password']

    db.session.commit()
    response = user_schema.dump(user)
    return jsonify(response)
#####################################################
@api.route('/carts/<id>', methods = ['POST', 'PUT'])
def update_cart(id):
    cart = Carts.query.get(id)
    cart.user_id = request.json['user_id']
    cart.item_size = request.json['item_size']
    cart.shipping_address = request.json['shipping_address']
    cart.custom_blend = request.json['custom_blend']

    db.session.commit()
    response = cart_schema.dump(cart)
    return jsonify(response)
######################################################
@api.route('/users/<id>', methods = ['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    response = user_schema.dump(user)
    return jsonify(response)
#######################################################
@api.route('/carts/<id>', methods = ['DELETE'])
def delete_cart(id):
    cart = Carts.query.get(id)
    db.session.delete(cart)
    db.session.commit()
    response = cart_schema.dump(cart)
    return jsonify(response)