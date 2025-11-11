from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j_conn import (
    driver, get_driver,
    log_view, log_like, add_to_wishlist, remove_from_wishlist,
    log_purchase, log_return, get_user_history, recommend_products,
    recommend_products_advanced,
    get_user_segment, item_based_recommendations, seasonal_promotions, manual_adjustment,
    add_to_cart, remove_from_cart, get_cart, checkout
)
from cf_engine import CollaborativeFiltering

app = Flask(__name__)
CORS(app)

cf = CollaborativeFiltering()
driver = get_driver()  # глобальный драйвер для всех

# ------------------------
# USERS
# ------------------------
@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    with driver.session() as s:
        s.run("CREATE (u:User {id:$id, name:$name, email:$email})",
              id=data["id"], name=data["name"], email=data["email"])
    return jsonify({"message": "User created"}), 201

@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    with driver.session() as s:
        result = s.run("MATCH (u:User {id:$id}) RETURN u.id AS id, u.name AS name, u.email AS email", id=user_id)
        user = result.single()
        if user:
            return jsonify(user.data())
        return jsonify({"error": "User not found"}), 404

@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json
    with driver.session() as s:
        s.run("MATCH (u:User {id:$id}) SET u.name=$name, u.email=$email", id=user_id, name=data["name"], email=data["email"])
    return jsonify({"message": "User updated"})

@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    with driver.session() as s:
        s.run("MATCH (u:User {id:$id}) DETACH DELETE u", id=user_id)
    return jsonify({"message": "User deleted"})

# ------------------------
# PRODUCTS
# ------------------------
@app.route("/products", methods=['POST'])
def create_product():
    data = request.get_json()
    with driver.session() as session:
        session.run("""
            MERGE (c:Category {name: $category})
            CREATE (p:Product {
                id:$id, name:$name, category:$category,
                price:$price, brand:$brand, description:$description,
                sku:$sku, images:$images, tags:$tags, options:$options,
                createdAt: datetime()
            })
            MERGE (p)-[:BELONGS_TO]->(c)
        """, **data)
    return jsonify({"message": "Product created"}), 201

@app.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    with driver.session() as s:
        result = s.run("MATCH (p:Product {id:$id}) RETURN p", id=product_id)
        product = result.single()
        if product:
            return jsonify(product["p"])
        return jsonify({"error": "Product not found"}), 404

@app.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.json
    with driver.session() as s:
        s.run("""
            MATCH (p:Product {id:$id})
            SET p.name=$name, p.category=$category, p.price=$price, p.brand=$brand
        """, **data, id=product_id)
    return jsonify({"message": "Product updated"})

@app.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    with driver.session() as s:
        s.run("MATCH (p:Product {id:$id}) DETACH DELETE p", id=product_id)
    return jsonify({"message": "Product deleted"})

# ------------------------
# SEARCH
# ------------------------
@app.route("/search", methods=["GET"])
def search_products():
    q = request.args.get("q", "")
    category = request.args.get("category")
    brand = request.args.get("brand")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort_by", "name")

    query = "MATCH (p:Product) WHERE toLower(p.name) CONTAINS toLower($q)"
    if category:
        query += " AND toLower(p.category) = toLower($category)"
    if brand:
        query += " AND toLower(p.brand) = toLower($brand)"
    if min_price is not None:
        query += " AND p.price >= $min_price"
    if max_price is not None:
        query += " AND p.price <= $max_price"
    query += f" RETURN p.id AS id, p.name AS name, p.category AS category, p.brand AS brand, p.price AS price"
    if sort_by in ["price", "name", "rating"]:
        query += f" ORDER BY p.{sort_by} ASC"

    with driver.session() as s:
        result = s.run(query, q=q, category=category, brand=brand, min_price=min_price, max_price=max_price)
        return jsonify([r.data() for r in result])

@app.route("/search/fulltext", methods=["GET"])
def search_fulltext():
    q = request.args.get("q", "")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort_by", "name")
    if not q:
        return jsonify([])

    query = """
        CALL db.index.fulltext.queryNodes("productFullTextIndex", $q) YIELD node, score
        WHERE ($min_price IS NULL OR node.price >= $min_price)
          AND ($max_price IS NULL OR node.price <= $max_price)
        RETURN node.id AS id, node.name AS name, node.category AS category, node.brand AS brand, node.price AS price, score
        ORDER BY score DESC
    """
    with driver.session() as s:
        result = s.run(query, q=q, min_price=min_price, max_price=max_price)
        return jsonify([r.data() for r in result])

# ------------------------
# HISTORY / USER ACTIONS
# ------------------------
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

@app.route("/recommend_advanced/<user_id>", methods=["GET"])
def recommend_advanced(user_id):
    recs = recommend_products_advanced(user_id)
    return jsonify(recs)

# ------------------------
# CART
# ------------------------
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

# ------------------------
# RECOMMENDATIONS
# ------------------------
@app.route("/recommendations/<user_id>", methods=["GET"])
def get_recommendations(user_id):
    algo = request.args.get("algo", "user_based")
    limit = int(request.args.get("limit", 10))
    cf.set_algorithm(algo)
    recs = cf.recommend(user_id, limit)
    return jsonify(recs)

@app.route("/user_segment/<user_id>", methods=["GET"])
def segment(user_id):
    seg = get_user_segment(user_id)
    return jsonify({"user_id": user_id, "segment": seg})

@app.route("/recommend/item/<product_id>", methods=["GET"])
def item_recommend(product_id):
    recs = item_based_recommendations(product_id)
    return jsonify(recs)

@app.route("/recommend/seasonal", methods=["GET"])
def seasonal():
    season = request.args.get("season")
    recs = seasonal_promotions(season)
    return jsonify(recs)

@app.route("/recommend/manual", methods=["GET"])
def manual():
    recs = manual_adjustment()
    return jsonify(recs)

# ------------------------
# COLLABORATIVE FILTERING
# ------------------------
@app.route("/cf/update_matrix", methods=["POST"])
def update_matrix():
    cf.update_preference_matrix()
    return {"message": "Preference matrix updated successfully."}

@app.route("/cf/recommend/<user_id>", methods=["GET"])
def cf_recommend(user_id):
    algo = request.args.get("algo", "user_based")
    cf.set_algorithm(algo)
    limit = int(request.args.get("limit", 10))
    recs = cf.recommend(user_id, limit)
    return jsonify(recs)

if __name__ == "__main__":
    app.run(debug=True)
