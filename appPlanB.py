from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j_conn import driver  # глобальный драйвер Neo4j
from cf_engine import CollaborativeFiltering
from neo4j_conn import (
    get_user_segment,
    item_based_recommendations,
    seasonal_promotions,
    manual_adjustment,
    log_view, log_like, add_to_wishlist, remove_from_wishlist,
    log_purchase, log_return, get_user_history, recommend_products,
    recommend_products_advanced,
    add_to_cart, remove_from_cart, get_cart, checkout
)

app = Flask(__name__)
CORS(app)

cf = CollaborativeFiltering()

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
@app.route("/products/crud", methods=['POST'])
def create_product():
    data = request.json
    with driver.session() as s:
        s.run("""
            MERGE (c:Category {name: $category})
            CREATE (p:Product {
                id:$id, name:$name, category:$category,
                price:$price, brand:$brand,
                description:$description, sku:$sku,
                images:$images, tags:$tags, options:$options,
                createdAt: datetime()
            })
            MERGE (p)-[:BELONGS_TO]->(c)
        """, **data)
    return jsonify({"message": "Product created"}), 201

@app.route("/products/crud/<product_id>", methods=["GET"])
def get_product(product_id):
    with driver.session() as s:
        result = s.run("MATCH (p:Product {id:$id}) RETURN p", id=product_id)
        product = result.single()
        if product:
            return jsonify(product["p"])
        return jsonify({"error": "Product not found"}), 404

@app.route("/products/crud/<sku>/review", methods=['POST'])
def add_review(sku):
    data = request.json
    with driver.session() as s:
        s.run("""
            MATCH (p:Product {sku:$sku})
            CREATE (r:Review {rating:$rating, comment:$comment, date:datetime()})
            CREATE (p)-[:HAS_REVIEW]->(r)
        """, sku=sku, rating=float(data.get("rating")), comment=data.get("comment",""))
    return jsonify({"message": "Review added"}), 201

@app.route("/products/crud/<sku>/reviews", methods=['GET'])
def get_reviews(sku):
    with driver.session() as s:
        result = s.run("""
            MATCH (p:Product {sku:$sku})-[:HAS_REVIEW]->(r:Review)
            RETURN r.rating AS rating, r.comment AS comment, r.date AS date
        """, sku=sku)
        reviews = [dict(r) for r in result]
        avg_rating = sum(r["rating"] for r in reviews)/len(reviews) if reviews else 0
    return jsonify({"reviews": reviews, "average_rating": round(avg_rating,2)})

@app.route("/products/crud/<sku>/price-history", methods=['POST'])
def update_price(sku):
    data = request.json
    new_price = data.get("price")
    with driver.session() as s:
        s.run("""
            MATCH (p:Product {sku:$sku})
            MERGE (h:PriceHistory {sku:$sku})
            CREATE (p)-[:CHANGED_PRICE]->(:PriceChange {oldPrice: p.price, newPrice:$new_price, date:datetime()})
            SET p.price=$new_price
        """, sku=sku, new_price=new_price)
    return jsonify({"message": "Price updated"})


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
    if category: query += " AND toLower(p.category)=toLower($category)"
    if brand: query += " AND toLower(p.brand)=toLower($brand)"
    if min_price is not None: query += " AND p.price >= $min_price"
    if max_price is not None: query += " AND p.price <= $max_price"
    query += f" RETURN p.id AS id, p.name AS name, p.category AS category, p.brand AS brand, p.price AS price"
    if sort_by in ["price","name","rating"]: query += f" ORDER BY p.{sort_by} ASC"

    with driver.session() as s:
        result = s.run(query, q=q, category=category, brand=brand, min_price=min_price, max_price=max_price)
        return jsonify([r.data() for r in result])

@app.route("/search/fulltext", methods=["GET"])
def search_fulltext():
    q = request.args.get("q", "")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort_by", "name")
    if not q: return jsonify([])
    query = """
        CALL db.index.fulltext.queryNodes("productFullTextIndex",$q) YIELD node, score
        WHERE ($min_price IS NULL OR node.price>=$min_price)
          AND ($max_price IS NULL OR node.price<=$max_price)
        RETURN node.id AS id,node.name AS name,node.category AS category,node.brand AS brand,node.price AS price,score
        ORDER BY score DESC
    """
    with driver.session() as s:
        result = s.run(query, q=q, min_price=min_price, max_price=max_price)
        return jsonify([r.data() for r in result])


# ------------------------
# HISTORY & USER ACTIONS
# ------------------------
@app.route("/history/view", methods=["POST"])
def view_product():
    data = request.json
    log_view(data["user_id"], data["product_id"])
    return jsonify({"message":"View logged"})

@app.route("/history/like", methods=["POST"])
def like_product():
    data = request.json
    log_like(data["user_id"], data["product_id"])
    return jsonify({"message":"Product liked"})

@app.route("/history/wishlist/add", methods=["POST"])
def wishlist_add():
    data = request.json
    add_to_wishlist(data["user_id"], data["product_id"])
    return jsonify({"message":"Added to wishlist"})

@app.route("/history/wishlist/remove", methods=["POST"])
def wishlist_remove():
    data = request.json
    remove_from_wishlist(data["user_id"], data["product_id"])
    return jsonify({"message":"Removed from wishlist"})

@app.route("/history/purchase", methods=["POST"])
def purchase():
    data = request.json
    log_purchase(data["user_id"], data["product_id"])
    return jsonify({"message":"Purchase logged"})

@app.route("/history/return", methods=["POST"])
def return_item():
    data = request.json
    log_return(data["user_id"], data["product_id"])
    return jsonify({"message":"Return logged"})

@app.route("/history/<user_id>", methods=["GET"])
def get_history(user_id):
    return jsonify(get_user_history(user_id))

@app.route("/history/recommend/<user_id>", methods=["GET"])
def recommend_history(user_id):
    recs = recommend_products(user_id)
    return jsonify(recs)

@app.route("/history/recommend_advanced/<user_id>", methods=["GET"])
def recommend_advanced_history(user_id):
    recs = recommend_products_advanced(user_id)
    return jsonify(recs)


# ------------------------
# CART
# ------------------------
@app.route("/cart/add", methods=["POST"])
def add_to_cart_route():
    data = request.json
    add_to_cart(data["user_id"], data["product_id"], data["quantity"])
    return jsonify({"message":"Item added to cart"})

@app.route("/cart/remove", methods=["POST"])
def remove_from_cart_route():
    data = request.json
    remove_from_cart(data["user_id"], data["product_id"])
    return jsonify({"message":"Item removed from cart"})

@app.route("/cart/<user_id>", methods=["GET"])
def view_cart_route(user_id):
    return jsonify(get_cart(user_id))

@app.route("/cart/checkout", methods=["POST"])
def checkout_route():
    data = request.json
    result = checkout(data["user_id"])
    return jsonify(result)


# ------------------------
# RECOMMENDATIONS & CF
# ------------------------
@app.route("/recommendations/<user_id>", methods=["GET"])
def get_recommendations(user_id):
    algo = request.args.get("algo","user_based")
    limit = int(request.args.get("limit",10))
    cf.set_algorithm(algo)
    recs = cf.recommend(user_id, limit)
    return jsonify(recs)

@app.route("/cf/update_matrix", methods=["POST"])
def update_matrix():
    cf.update_preference_matrix()
    return {"message":"Preference matrix updated."}

@app.route("/cf/recommend/<user_id>", methods=["GET"])
def cf_recommend(user_id):
    algo = request.args.get("algo","user_based")
    cf.set_algorithm(algo)
    limit = int(request.args.get("limit",10))
    recs = cf.recommend(user_id, limit)
    return jsonify(recs)


if __name__ == "__main__":
    app.run(debug=True)
