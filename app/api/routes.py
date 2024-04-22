from app import db
from flask import request, jsonify, redirect
from app.models import User, Carts, Orders, user_schema, users_schema, cart_schema, carts_schema, order_schema, orders_schema
from . import api
import stripe
import requests
from flask_cors import cross_origin
import json

stripe.api_key = 'sk_test_51P21ugLpIM9qGk22XNvAbtnZLykj4qXi2yMC3aRzMvRvDEOalWBJMQDNUE8MPiqx6bMfVZtnKuovVdfa5F94aYuI00zXYonIGk'
endpoint_secret = 'whsec_EuGg7bLhjeeO98cFjj3ILL0QGfDou8vv'  # The signing secret from Stripe Dashboard

@api.route('/api/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    # Process the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)

    return jsonify({'status': 'success'}), 200

def handle_checkout_session(session):
    user_id = session.get('client_reference_id')
    cart = Carts.query.filter_by(user_id=user_id).first()

    if cart:
        create_order_from_cart(cart, session)
        clear_user_cart(cart)
        db.session.commit()

def create_order_from_cart(cart, session):
    shipping_details = session['shipping']
    new_order = Orders(user_id=cart.user_id, custom_blend=cart.custom_blend, totalPrice=cart.totalPrice, shipping_address=str(shipping_details))
    db.session.add(new_order)

def clear_user_cart(cart):
    db.session.delete(cart)

###################################################
@api.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    
    cart_items = Carts.query.first()
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
                        'name': 'Your Blend Total',
                    },
                },
                'quantity': 1,
            }
        ],
        mode='payment',
        success_url='http://localhost:5173/',
        cancel_url='http://localhost:5173/checkout'
    )

    return jsonify(id=session.id, url=session.url)  # Send back the URL to the client

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
@api.route('/cart/item/<string:itemName>', methods=['DELETE'])
@cross_origin(supports_credentials=True)
def delete_item(itemName):
    user_id = request.headers.get('User')
    if not user_id:
        print("No User ID provided")
        return jsonify({'error': 'Unauthorized access'}), 401

    print(f"Attempting to remove item: {itemName} for user: {user_id}")
    cart = Carts.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404

    try:
        items = json.loads(cart.custom_blend)
        items = [item for item in items if item['name'] != itemName]
        cart.custom_blend = json.dumps(items)
        total_price = sum(item['totalPrice'] * item['quantity'] for item in items)
        cart.totalPrice = total_price

        db.session.commit()
        return jsonify({'message': 'Item removed', 'updatedCart': items, 'totalPrice': total_price}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update cart', 'message': str(e)}), 500
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

        data = request.get_json(force=True)  # Make sure to parse incoming JSON correctly
        print(f'Data received: {data}')

        cart = Carts.query.filter_by(user_id=user_id).first()
        if not cart:
            # If there's no existing cart, create a new one
            cart = Carts(user_id=user_id, custom_blend=json.dumps(data), totalPrice=0)
            db.session.add(cart)

        existing_items = json.loads(cart.custom_blend) if cart.custom_blend else []

        # Create a dictionary for quick access to existing items by name
        item_dict = {item['name']: item for item in existing_items}

        # Merge incoming items with existing ones
        for new_item in data:
            if new_item['name'] in item_dict:
                # Update existing item quantities and totalPrice
                existing_item = item_dict[new_item['name']]
                existing_item['quantity'] += new_item['quantity']
                existing_item['totalPrice'] = round(existing_item['quantity'] * (existing_item['totalPrice'] / (existing_item['quantity'] - new_item['quantity'])), 2)
            else:
                # Add new item if it doesn't exist
                item_dict[new_item['name']] = new_item

        # Calculate the total price from updated items
        totalPrice = sum(item['totalPrice'] * item['quantity'] for item in item_dict.values())
        totalPrice = round(totalPrice, 2)
        print(f'Calculated Total Price: {totalPrice}')

        # Update the cart with merged items
        cart.custom_blend = json.dumps(list(item_dict.values()))
        cart.totalPrice = totalPrice

        db.session.commit()
        return jsonify(cart_schema.dump(cart)), 200
    except Exception as e:
        db.session.rollback()
        print(f'An error occurred: {e}')
        return jsonify({'error': 'Internal Server Error'}), 500

#####################################################
@api.route('/update-cart-item', methods=['POST'])
def update_cart_item():
    print("Request to update cart item received")
    user_id = request.headers.get('User')
    if not user_id:
        print("Unauthorized access attempt without User ID")
        return jsonify({'error': 'Unauthorized access'}), 401

    data = request.get_json()
    print(f"Data received for update: {data}")
    if not data:
        print("No data provided in the request")
        return jsonify({'error': 'No data provided'}), 400

    try:
        cart = Carts.query.filter_by(user_id=user_id).first()
        if not cart:
            print(f"No cart found for user: {user_id}")
            return jsonify({'error': 'Cart not found'}), 404

        print(f"Existing cart items before update: {cart.custom_blend}")
        cart_items = json.loads(cart.custom_blend) if cart.custom_blend else []

        updated_items = []
        for item_update in data:
            # Convert quantity to integer if necessary
            item_update['quantity'] = int(item_update['quantity'])
            item = next((item for item in cart_items if item['name'] == item_update['name']), None)
            if item:
                item['quantity'] = item_update['quantity']
                print(f"Updating item: {item['name']} to quantity {item['quantity']}")
            else:
                print(f"Adding new item to cart: {item_update['name']}")
                cart_items.append(item_update)
            updated_items.append(item_update)

        # Update the cart's custom_blend with the modified list of items
        cart.custom_blend = json.dumps(cart_items)
        print(f"Cart items after update: {cart.custom_blend}")

        # Recalculate total price
        totalPrice = sum(item['totalPrice'] * item['quantity'] for item in cart_items)
        cart.totalPrice = round(totalPrice, 2)
        print(f"Updated total price: {cart.totalPrice}")

        db.session.commit()
        return jsonify({'updatedItems': cart_items, 'totalPrice': cart.totalPrice}), 200
    except Exception as e:
        print(f"An error occurred during cart update: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update cart', 'message': str(e)}), 500