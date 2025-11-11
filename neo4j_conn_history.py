from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "12345678"   # свой пароль Neo4j

driver = GraphDatabase.driver(uri, auth=(user, password))

# --- Основные действия пользователя ---

def log_view(user_id, product_id):
    with driver.session() as s:
        s.run("""
            MERGE (u:User {id:$user_id})
            MERGE (p:Product {id:$product_id})
            CREATE (u)-[:VIEWED {time:datetime()}]->(p)
        """, user_id=user_id, product_id=product_id)

def log_like(user_id, product_id):
    with driver.session() as s:
        s.run("""
            MERGE (u:User {id:$user_id})
            MERGE (p:Product {id:$product_id})
            MERGE (u)-[:LIKED]->(p)
        """, user_id=user_id, product_id=product_id)

def add_to_wishlist(user_id, product_id):
    with driver.session() as s:
        s.run("""
            MERGE (u:User {id:$user_id})
            MERGE (p:Product {id:$product_id})
            MERGE (u)-[:WISHLISTED]->(p)
        """, user_id=user_id, product_id=product_id)

def remove_from_wishlist(user_id, product_id):
    with driver.session() as s:
        s.run("""
            MATCH (u:User {id:$user_id})-[r:WISHLISTED]->(p:Product {id:$product_id})
            DELETE r
        """, user_id=user_id, product_id=product_id)

def log_purchase(user_id, product_id):
    with driver.session() as s:
        s.run("""
            MERGE (u:User {id:$user_id})
            MERGE (p:Product {id:$product_id})
            CREATE (u)-[:PURCHASED {time:datetime()}]->(p)
        """, user_id=user_id, product_id=product_id)

def log_return(user_id, product_id):
    with driver.session() as s:
        s.run("""
            MATCH (u:User {id:$user_id})-[r:PURCHASED]->(p:Product {id:$product_id})
            CREATE (u)-[:RETURNED {time:datetime()}]->(p)
        """, user_id=user_id, product_id=product_id)

def get_user_history(user_id):
    with driver.session() as s:
        res = s.run("""
            MATCH (u:User {id:$user_id})-[r]->(p:Product)
            RETURN type(r) AS action, p.id AS product_id, r.time AS time
            ORDER BY r.time DESC
        """, user_id=user_id)
        return [r.data() for r in res]

def recommend_products(user_id, limit=5):
    """
    Рекомендуем товары, основываясь на:
    - Просмотрах и лайках пользователя
    - Похожих товарах (те, которые лайкали другие пользователи)
    """
    with driver.session() as s:
        result = s.run("""
            MATCH (u:User {id:$user_id})-[:VIEWED|LIKED]->(p:Product)
            WITH collect(p) AS user_products
            MATCH (other:User)-[:LIKED]->(p2:Product)
            WHERE other.id <> $user_id AND p2 IN user_products
            MATCH (other)-[:LIKED]->(rec:Product)
            WHERE NOT ( (u)-[:PURCHASED]->(rec) OR (u)-[:LIKED]->(rec) )
            RETURN rec.id AS product_id, rec.name AS name, rec.category AS category, rec.price AS price, count(*) AS score
            ORDER BY score DESC
            LIMIT $limit
        """, user_id=user_id, limit=limit)
        return [r.data() for r in result]
    
def recommend_products_advanced(user_id, limit=5):
    """
    Персонализированные рекомендации:
    - Лайки: вес 3
    - Wishlist: вес 2
    - Просмотры: вес 1
    Исключаем:
    - Уже купленные
    - Возвращённые товары
    """
    with driver.session() as s:
        result = s.run("""
            MATCH (u:User {id:$user_id})
            
            // Получаем интерес пользователя
            OPTIONAL MATCH (u)-[l:LIKED]->(p1:Product)
            OPTIONAL MATCH (u)-[w:WISHLISTED]->(p2:Product)
            OPTIONAL MATCH (u)-[v:VIEWED]->(p3:Product)
            
            WITH u,
                 collect(p1) AS liked,
                 collect(p2) AS wish,
                 collect(p3) AS viewed

            UNWIND liked + wish + viewed AS user_products

            // Находим похожие товары через других пользователей
            MATCH (other:User)-[o_l:LIKED|:WISHLISTED]->(user_products)
            WHERE other.id <> $user_id

            MATCH (other)-[r:LIKED|:WISHLISTED|:VIEWED]->(rec:Product)
            
            // Исключаем уже купленные и возвращённые
            WHERE NOT ( (u)-[:PURCHASED]->(rec) OR (u)-[:RETURNED]->(rec) OR rec IN user_products )

            WITH rec,
                 sum(
                     CASE WHEN type(r)="LIKED" THEN 3
                          WHEN type(r)="WISHLISTED" THEN 2
                          WHEN type(r)="VIEWED" THEN 1
                     END
                 ) AS score

            RETURN rec.id AS product_id, rec.name AS name, rec.category AS category, rec.price AS price, score
            ORDER BY score DESC
            LIMIT $limit
        """, user_id=user_id, limit=limit)
        return [r.data() for r in result]
