from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j_conn import (
    log_view, log_like, add_to_wishlist, remove_from_wishlist,
    log_purchase, log_return, get_user_history, recommend_products
)

app = Flask(__name__)
CORS(app)

@app.route("/view", methods=["POST"])
def view_product():
    data = request.json
    log_view(data["user_id"], data["product_id"])
    return jsonify({"message": "View logged"})

@app.route("/like", methods=["POST"])
def like_product():
    data = request.json
    log_like(data["user_id"], data["product_id"])
    return jsonify({"message": "Product liked"})

@app.route("/wishlist/add", methods=["POST"])
def wishlist_add():
    data = request.json
    add_to_wishlist(data["user_id"], data["product_id"])
    return jsonify({"message": "Added to wishlist"})

@app.route("/wishlist/remove", methods=["POST"])
def wishlist_remove():
    data = request.json
    remove_from_wishlist(data["user_id"], data["product_id"])
    return jsonify({"message": "Removed from wishlist"})

@app.route("/purchase", methods=["POST"])
def purchase():
    data = request.json
    log_purchase(data["user_id"], data["product_id"])
    return jsonify({"message": "Purchase logged"})

@app.route("/return", methods=["POST"])
def return_item():
    data = request.json
    log_return(data["user_id"], data["product_id"])
    return jsonify({"message": "Return logged"})

@app.route("/history/<user_id>", methods=["GET"])
def history(user_id):
    return jsonify(get_user_history(user_id))


@app.route("/recommend/<user_id>", methods=["GET"])
def recommend(user_id):
    recs = recommend_products(user_id)
    return jsonify(recs)
from neo4j_conn import recommend_products_advanced

@app.route("/recommend_advanced/<user_id>", methods=["GET"])
def recommend_advanced(user_id):
    recs = recommend_products_advanced(user_id)
    return jsonify(recs)

if __name__ == "__main__":
    app.run(debug=True)
