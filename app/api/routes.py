from app import db
from flask import request, jsonify, redirect
from app.models import User, Carts, Orders, user_schema, users_schema, cart_schema, carts_schema, order_schema, orders_schema
from . import api
import stripe
import requests
from flask_cors import cross_origin
import json
import logging

stripe.api_key = 'sk_test_51P21ugLpIM9qGk22XNvAbtnZLykj4qXi2yMC3aRzMvRvDEOalWBJMQDNUE8MPiqx6bMfVZtnKuovVdfa5F94aYuI00zXYonIGk'
endpoint_secret = 'whsec_7EFy7XyNUcXEQcFCBo7AgtBrTPfYym7j'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@api.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    logging.info("Starting the creation of a checkout session...")
    cart_items = Carts.query.first()
    if cart_items:
        logging.info(f"Found cart items, total price before rounding: {cart_items.totalPrice}")
        totalPrice = int(round(cart_items.totalPrice, 2) * 100)
        logging.info(f"Total price after converting to cents: {totalPrice}")
    else:
        totalPrice = 0
        logging.info("No cart items found, setting total price to 0.")

    try:
        logging.info("Attempting to create Stripe checkout session...")
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            shipping_address_collection={
                'allowed_countries': ['US', 'CA', 'GB'],
            },
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': totalPrice,
                    'product_data': {
                        'name': 'Your Blend Total',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://seasonality-9c65a.web.app/',
            cancel_url='https://seasonality-9c65a.web.app/api/checkout',
            metadata={'user_uid': cart_items.user_id}
        )
        logging.info(f"Stripe session created successfully, session ID: {session.id}")
    except Exception as e:
        logging.error(f"Failed to create Stripe session: {str(e)}")
        return jsonify({'error': str(e)}), 500

    return jsonify(id=session.id, url=session.url)
############################################################
@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        logging.info("Successfully constructed webhook event.")
    except ValueError as e:
        logging.error(f"Invalid payload: {str(e)}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Invalid signature: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_uid = session['metadata'].get('user_uid')
        
        cart = Carts.query.filter_by(user_id=user_uid).first()
        if not cart:
            logging.error("Cart not found for user UID: {}".format(user_uid))
            return jsonify({'error': 'Cart not found'}), 404

        # Process order details
        if isinstance(cart.custom_blend, str):
            order_details = cart.custom_blend  # Assuming it's already a JSON string
        else:
            order_details = json.dumps(cart.custom_blend)  # Convert dict to JSON string if needed

        # Extract shipping details
        shipping = session.get('shipping', {})
        shipping_address = shipping.get('address', {})
        
        # Create a new order in the database
        new_order = Orders(
            order_details=order_details,
            totalPrice=cart.totalPrice,
            uid=user_uid,
            shipping_name=shipping.get('name', ''),
            shipping_line1=shipping_address.get('line1', ''),
            shipping_city=shipping_address.get('city', ''),
            shipping_country=shipping_address.get('country', ''),
            shipping_postal_code=shipping_address.get('postal_code', '')
        )
        db.session.add(new_order)

        # Clear the cart after processing
        db.session.delete(cart)
        db.session.commit()
        logging.info("Order processed and cart cleared for user UID: {}".format(user_uid))
        return jsonify({'message': 'Order processed and cart cleared'}), 200

    return jsonify({'message': 'Webhook received but not processed'}), 200
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