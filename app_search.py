@app.route("/search", methods=["GET"])
def search_products():
    """
    Параметры запроса:
    - q: строка поиска
    - category: фильтр по категории
    - brand: фильтр по бренду
    - min_price, max_price: фильтр по цене
    - sort_by: price, name, rating
    """
    q = request.args.get("q", "")
    category = request.args.get("category")
    brand = request.args.get("brand")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort_by", "name")  # default sort

    query = """
        MATCH (p:Product)
        WHERE toLower(p.name) CONTAINS toLower($q)
    """

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
    """
    Параметры:
    - q: строка поиска
    - min_price, max_price
    - sort_by: price, name, rating
    """
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
