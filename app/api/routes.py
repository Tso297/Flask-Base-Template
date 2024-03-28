from app import db
from flask import request, jsonify
from app.models import User, Orders, user_schema, users_schema, order_schema, orders_schema
from . import api


###################################################
@api.route('/users', methods = ['POST'])
def create_user():
    username = request.json['username']
    email = request.json['email']
    phone_number = request.json['phone_number']
    password = request.json['password']

    user = User(username, email, phone_number, password)

    db.session.add(user)
    db.session.commit()

    response = user_schema.dump(user)
    return jsonify(response)
###################################################
@api.route('/orders', methods = ['POST'])
def create_order():
    user_id = request.json['user_id']
    item_size = request.json['item_size']
    shipping_address = request.json['shipping_address']
    custom_blend = request.json['custom_blend']


    order = Orders(user_id, item_size, shipping_address, custom_blend)

    db.session.add(order)
    db.session.commit()

    response = order_schema.dump(order)
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
@api.route('/orders', methods = ['GET'])
def get_orders():
    orders = Orders.query.all()
    response = orders_schema.dump(orders)
    return jsonify(response)
####################################################
@api.route('/orders/<id>', methods = ['GET'])
def get_single_order(id):
    order = Orders.query.get(id)
    response = order_schema.dump(order)
    return jsonify(response)
#####################################################
@api.route('/users/<id>', methods = ['POST', 'PUT'])
def update_user(id):
    user = User.query.get(id)
    user.username = request.json['username']
    user.email = request.json['email']
    user.phone_number = request.json['phone_number']
    user.password = request.json['password']

    db.session.commit()
    response = user_schema.dump(user)
    return jsonify(response)
#####################################################
@api.route('/orders/<id>', methods = ['POST', 'PUT'])
def update_order(id):
    order = Orders.query.get(id)
    order.user_id = request.json['user_id']
    order.item_size = request.json['item_size']
    order.shipping_address = request.json['shipping_address']
    order.custom_blend = request.json['custom_blend']

    db.session.commit()
    response = order_schema.dump(order)
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
@api.route('/orders/<id>', methods = ['DELETE'])
def delete_order(id):
    order = Orders.query.get(id)
    db.session.delete(order)
    db.session.commit()
    response = order_schema.dump(order)
    return jsonify(response)

