from flask import Flask, request, jsonify
from neo4j_conn import driver

app = Flask(__name__)

# ------------------------
# Создание пользователя
# ------------------------
@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    with driver.session() as s:
        s.run("CREATE (u:User {id:$id, name:$name, email:$email})",
              id=data["id"], name=data["name"], email=data["email"])
    return jsonify({"message": "User created"}), 201

# ------------------------
# Получение пользователя
# ------------------------
@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    with driver.session() as s:
        result = s.run("MATCH (u:User {id:$id}) RETURN u.id AS id, u.name AS name, u.email AS email", id=user_id)
        user = result.single()
        if user:
            return jsonify(user.data())
        return jsonify({"error": "User not found"}), 404

# ------------------------
# Обновление пользователя
# ------------------------
@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json
    with driver.session() as s:
        s.run("MATCH (u:User {id:$id}) SET u.name=$name, u.email=$email", id=user_id, name=data["name"], email=data["email"])
    return jsonify({"message": "User updated"})

# ------------------------
# Удаление пользователя
# ------------------------
@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    with driver.session() as s:
        s.run("MATCH (u:User {id:$id}) DETACH DELETE u", id=user_id)
    return jsonify({"message": "User deleted"})

# Создание продукта
@app.route("/products", methods=["POST"])
def create_product():
    data = request.json
    with driver.session() as s:
        s.run("""
            CREATE (p:Product {
                id:$id, name:$name, category:$category,
                price:$price, brand:$brand
            })
        """, **data)
    return jsonify({"message": "Product created"}), 201

# Получение продукта
@app.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    with driver.session() as s:
        result = s.run("MATCH (p:Product {id:$id}) RETURN p", id=product_id)
        product = result.single()
        if product:
            return jsonify(product["p"])
        return jsonify({"error": "Product not found"}), 404

# Обновление продукта
@app.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.json
    with driver.session() as s:
        s.run("""
            MATCH (p:Product {id:$id})
            SET p.name=$name, p.category=$category, p.price=$price, p.brand=$brand
        """, **data, id=product_id)
    return jsonify({"message": "Product updated"})

# Удаление продукта
@app.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    with driver.session() as s:
        s.run("MATCH (p:Product {id:$id}) DETACH DELETE p", id=product_id)
    return jsonify({"message": "Product deleted"})

from cf_engine import CollaborativeFiltering
cf = CollaborativeFiltering()

@app.route("/recommendations/<user_id>", methods=["GET"])
def get_recommendations(user_id):
    algo = request.args.get("algo", "user_based")
    limit = int(request.args.get("limit", 10))
    cf.set_algorithm(algo)
    recs = cf.recommend(user_id, limit)
    return jsonify(recs)
