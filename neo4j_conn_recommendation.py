from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "12345678"  # поменяй на свой пароль
driver = GraphDatabase.driver(uri, auth=(user, password))

# ------------------------
# Пользователи и сегментация
# ------------------------
def get_user_segment(user_id):
    """
    Простейшая сегментация:
    - 'newbie' - <3 покупок
    - 'active' - 3-10 покупок
    - 'vip' - >10 покупок
    """
    with driver.session() as s:
        res = s.run("""
            MATCH (u:User {id:$user_id})-[:PURCHASED]->(p:Product)
            RETURN count(p) AS purchases
        """, user_id=user_id)
        count = res.single()["purchases"]
        if count < 3:
            return "newbie"
        elif count <= 10:
            return "active"
        else:
            return "vip"

# ------------------------
# Item-based рекомендации
# ------------------------
def item_based_recommendations(product_id, limit=5):
    """
    Рекомендуем похожие товары по той же категории или тегам
    """
    with driver.session() as s:
        result = s.run("""
            MATCH (p:Product {id:$product_id})
            MATCH (p)-[:IN_CATEGORY]->(c:Category)<-[:IN_CATEGORY]-(rec:Product)
            WHERE rec.id <> $product_id
            RETURN rec.id AS id, rec.name AS name, rec.price AS price, rec.category AS category
            LIMIT $limit
        """, product_id=product_id, limit=limit)
        return [r.data() for r in result]

# ------------------------
# Сезонные/акционные рекомендации
# ------------------------
def seasonal_promotions(season=None, limit=5):
    """
    Возвращает товары с тегом сезона или акционные
    """
    with driver.session() as s:
        query = """
            MATCH (p:Product)
            WHERE $season IS NULL OR p.season = $season OR p.promo = true
            RETURN p.id AS id, p.name AS name, p.price AS price, p.category AS category
            LIMIT $limit
        """
        result = s.run(query, season=season, limit=limit)
        return [r.data() for r in result]

# ------------------------
# Ручная корректировка
# ------------------------
def manual_adjustment():
    """
    Товары с весом (weight) больше 0 будут продвигаться
    """
    with driver.session() as s:
        result = s.run("""
            MATCH (p:Product)
            WHERE exists(p.weight) AND p.weight > 0
            RETURN p.id AS id, p.name AS name, p.price AS price, p.category AS category, p.weight AS weight
            ORDER BY p.weight DESC
        """)
        return [r.data() for r in result]
