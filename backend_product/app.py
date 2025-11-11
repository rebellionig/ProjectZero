from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j_conn import get_driver

app = Flask(__name__)
CORS(app)

driver = get_driver()

# --- Создание товара ---
@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    category = data.get("category")
    price = data.get("price")
    sku = data.get("sku")
    images = data.get("images", [])
    tags = data.get("tags", [])
    options = data.get("options", {})

    with driver.session() as session:
        session.run("""
            MERGE (c:Category {name: $category})
            CREATE (p:Product {
                name: $name,
                description: $description,
                price: $price,
                sku: $sku,
                images: $images,
                tags: $tags,
                options: $options,
                createdAt: datetime()
            })
            MERGE (p)-[:BELONGS_TO]->(c)
        """, name=name, description=description, price=price,
           sku=sku, images=images, tags=tags, options=options, category=category)

    return jsonify({"message": "Product created"}), 201

# --- Получение всех товаров с фильтрами ---
@app.route('/products', methods=['GET'])
def get_products():
    category = request.args.get("category")
    sort_by = request.args.get("sort", "name")
    min_price = float(request.args.get("min_price", 0))
    max_price = float(request.args.get("max_price", 999999))

    query = """
    MATCH (p:Product)
    WHERE p.price >= $min_price AND p.price <= $max_price
    """
    if category:
        query += " MATCH (p)-[:BELONGS_TO]->(c:Category {name: $category})"

    query += f" RETURN p ORDER BY p.{sort_by}"

    with driver.session() as session:
        result = session.run(query, category=category, min_price=min_price, max_price=max_price)
        products = [record["p"] for record in result]

    return jsonify(products)

# --- Добавление отзыва ---
@app.route('/products/<sku>/review', methods=['POST'])
def add_review(sku):
    data = request.get_json()
    rating = float(data.get("rating"))
    comment = data.get("comment","")

    with driver.session() as session:
        session.run("""
            MATCH (p:Product {sku: $sku})
            CREATE (r:Review {rating: $rating, comment: $comment, date: datetime()})
            CREATE (p)-[:HAS_REVIEW]->(r)
        """, sku=sku, rating=rating, comment=comment)

    return jsonify({"message": "Review added"}), 201

# --- Получение отзывов ---
@app.route('/products/<sku>/reviews', methods=['GET'])
def get_reviews(sku):
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Product {sku: $sku})-[:HAS_REVIEW]->(r:Review)
            RETURN r.rating AS rating, r.comment AS comment, r.date AS date
        """, sku=sku)
        reviews = [dict(record) for record in result]
        if reviews:
            avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
        else:
            avg_rating = 0.0
    return jsonify({"reviews": reviews,"average_rating": round(avg_rating,2)})

# --- История изменений цены ---
@app.route('/products/<sku>/price-history', methods=['POST'])
def update_price(sku):
    data = request.get_json()
    new_price = data.get("price")

    with driver.session() as session:
        session.run("""
            MATCH (p:Product {sku: $sku})
            MERGE (h:PriceHistory {sku: $sku})
            CREATE (p)-[:CHANGED_PRICE]->(:PriceChange {oldPrice: p.price, newPrice: $new_price, date: datetime()})
            SET p.price = $new_price
        """, sku=sku, new_price=new_price)

    return jsonify({"message": "Price updated"})


if __name__ == "__main__":
    app.run(debug=True)
