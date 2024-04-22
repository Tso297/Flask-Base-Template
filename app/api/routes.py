from app import db
from flask import request, jsonify, redirect
from app.models import User, Carts, Orders, user_schema, users_schema, cart_schema, carts_schema, order_schema, orders_schema
from . import api
import stripe
import requests
from flask_cors import cross_origin
import json

stripe.api_key = 'sk_test_51P21ugLpIM9qGk22XNvAbtnZLykj4qXi2yMC3aRzMvRvDEOalWBJMQDNUE8MPiqx6bMfVZtnKuovVdfa5F94aYuI00zXYonIGk'

@api.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    cart_items = Carts.query.first()
    print(cart_items.totalPrice)
    if cart_items:
        totalPrice = int(round(cart_items.totalPrice, 2) * 100) # Assuming totalPrice is a field in your Cart model
        print(totalPrice)
    else:
        totalPrice = 0

    session = stripe.checkout.Session.create(
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': totalPrice,
                    'product_data': {
                        'name': 'Your Blends',
                    },
                },
                'quantity': 1,
            }
        ],
        mode='payment',
        success_url='http://localhost:5173/',
        cancel_url='http://localhost:5173/'
    )

    return jsonify(id=session.id, url=session.url)  # Send back the URL to the client


# @app.route('/success', methods=['GET'])
# def order_success():
#     session_id = request.args.get('session_id')
#     if session_id:
#         # Here you can handle post-payment logic, like creating an order record
#         # Logic to create an order or similar action
#         return 'Order created successfully', 200
#     return 'No session ID provided', 400

# Need to figure out how to make the success url hit my api for a remove

###################################################
@api.route('/checkout', methods = ['POST'])
def create_cart():
    user_id = request.headers.get('User')

    # Retrieve the JSON data sent from the client
    received_data = request.get_json()

    # Debug: Print the received data to see its structure
    print("Received data:", received_data)

    # Ensure received_data is always a list
    if isinstance(received_data, dict):
        received_data = [received_data]  # Convert to list if it's a single dictionary

    totalPrice = 0
    # Calculate the total price
    for blend in received_data:
        if 'totalPrice' not in blend:
            return jsonify({"error": "Missing totalPrice in some items"}), 400
        totalPrice += blend['totalPrice']  # Sum the totalPrice from each blend
    totalPrice = round(totalPrice, 2)  # Round the totalPrice after summing

    # Convert custom_blend to string for database storage
    custom_blend_str = str(received_data)



    # Create a new Carts object and add it to the database
    cart = Carts(custom_blend=custom_blend_str, totalPrice=totalPrice, user_id=user_id)
    db.session.add(cart)
    db.session.commit()

    # Serialize the cart data for the response
    response = cart_schema.dump(cart)
    return jsonify(response)
####################################################
@api.route('/orders', methods = ['POST'])
def create_order():
    order = []
    for blend in request.json:
        order.append(blend)

    totalPrice = 0
    for i in range(len(order)):
        totalPrice += order[i]['totalPrice']
        totalPrice = round(totalPrice, 2)

    order = str(order)
    order = Orders(order, totalPrice)

    db.session.add(Orders(order=order, totalPrice=totalPrice))
    db.session.commit()

    response = order_schema.dump(order)
    return jsonify(response)

####################################################
@api.route('/cart', methods=['GET'])
def get_carts():
    user_id = request.headers.get('User')
    if not user_id:
        return jsonify({'error': 'User ID is missing'}), 400

    cart = Carts.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404

    # Note: Use dump(cart, many=False) for a single object. If `cart` could be a list, use `many=True`.
    response = carts_schema.dump(cart, many=False)  # Set many=False as we're dumping a single cart object
    print(response)
    return jsonify(response)

######################################################
@api.route('/cart', methods = ['DELETE'])
def delete_cart(id):
    cart = Carts.query.get(id)
    db.session.delete(cart)
    db.session.commit()
    response = cart_schema.dump(cart)
    return jsonify(response)
######################################################
@api.route('/update-cart', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:5173', methods=['POST'], allow_headers=['Content-Type', 'Authorization', 'User'])
def update_cart():
    try:
        print('Request to update cart received')
        user_id = request.headers.get('User')
        print(f'User ID: {user_id}')

        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400

        data = request.get_json()
        print(f'Data received: {data}')

        # Calculate total price
        totalPrice = 0
        for item in data:
            totalPrice += item.get('totalPrice', 0) * item.get('quantity', 1)
        totalPrice = round(totalPrice, 2)
        print(f'Calculated Total Price: {totalPrice}')

        cart = Carts.query.filter_by(user_id=user_id).first()
        print(f'Existing cart: {cart}')

        if not cart:
            cart = Carts(user_id=user_id, custom_blend=json.dumps(data), totalPrice=totalPrice)
            db.session.add(cart)
        else:
            # Assuming custom_blend is a JSON field and we can append data to it
            existing_data = json.loads(cart.custom_blend) if cart.custom_blend else []
            existing_data.extend(data)
            cart.custom_blend = json.dumps(existing_data)
            cart.totalPrice = totalPrice  # Update total price

        db.session.commit()
        return jsonify(cart_schema.dump(cart)), 200
    except Exception as e:
        print(f'An error occurred: {e}')
        return jsonify({'error': 'Internal Server Error'}), 500
#######################################################
@api.route('/users', methods = ['POST'])
def create_user():

    displayName = request.json['displayName']
    user_id = request.json['uid']
    email = request.json['email']
    user = User(displayName, user_id, email)

    db.session.add(user)
    db.session.commit()

    response = user_schema.dump(user)
    return jsonify(response)
#####################################################
@api.route('/update-cart-item', methods=['POST'])
def update_cart_item():
    user_id = request.headers.get('User')
    if not user_id:
        return jsonify({'error': 'Unauthorized access'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        print(f"Received update for user {user_id} with the following data: {data}")
        cart = Carts.query.filter_by(user_id=user_id).first()
        if not cart:
            return jsonify({'error': 'Cart not found'}), 404

        # Assume cart.custom_blend is stored in JSON and needs to be parsed
        cart_items = json.loads(cart.custom_blend) if cart.custom_blend else []

        updated_items = []
        for item_update in data:
            # Convert quantity to integer
            if 'quantity' in item_update:
                try:
                    item_update['quantity'] = int(item_update['quantity'])
                except ValueError:
                    return jsonify({'error': 'Invalid quantity value'}), 400

            # Find and update the item by name
            item = next((item for item in cart_items if item['name'] == item_update['name']), None)
            if item:
                item['quantity'] = item_update['quantity']
            else:
                # Add new item if it does not exist in the cart
                cart_items.append(item_update)

            updated_items.append(item_update)

        # Update the cart's custom_blend with the modified list of items
        cart.custom_blend = json.dumps(cart_items)
        db.session.commit()

        return jsonify(updated_items), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Failed to update cart'}), 500