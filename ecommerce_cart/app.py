from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j_conn import add_to_cart, remove_from_cart, get_cart, checkout

app = Flask(__name__)
CORS(app)

@app.route("/cart/add", methods=["POST"])
def add_item():
    data = request.json
    add_to_cart(data["user_id"], data["product_id"], data["quantity"])
    return jsonify({"message": "Item added to cart"})

@app.route("/cart/remove", methods=["POST"])
def remove_item():
    data = request.json
    remove_from_cart(data["user_id"], data["product_id"])
    return jsonify({"message": "Item removed from cart"})

@app.route("/cart/<user_id>", methods=["GET"])
def view_cart(user_id):
    cart = get_cart(user_id)
    return jsonify(cart)

@app.route("/checkout", methods=["POST"])
def do_checkout():
    data = request.json
    result = checkout(data["user_id"])
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
