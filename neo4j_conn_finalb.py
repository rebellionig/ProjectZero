# neo4j_conn.py
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_driver():
    return driver

def close_driver():
    driver.close()


# ------------------------
# Cart Operations
# ------------------------
class Cart:
    @staticmethod
    def add_to_cart(user_id, product_id, quantity):
        with driver.session() as s:
            s.run("""
                MERGE (u:User {id:$user_id})
                MERGE (p:Product {id:$product_id})
                MERGE (u)-[r:HAS_IN_CART]->(p)
                ON CREATE SET r.quantity=$quantity
                ON MATCH SET r.quantity = r.quantity + $quantity
            """, user_id=user_id, product_id=product_id, quantity=quantity)

    @staticmethod
    def remove_from_cart(user_id, product_id):
        with driver.session() as s:
            s.run("""
                MATCH (u:User {id:$user_id})-[r:HAS_IN_CART]->(p:Product {id:$product_id})
                DELETE r
            """, user_id=user_id, product_id=product_id)

    @staticmethod
    def get_cart(user_id):
        with driver.session() as s:
            res = s.run("""
                MATCH (u:User {id:$user_id})-[r:HAS_IN_CART]->(p:Product)
                RETURN p.id AS id, p.name AS name, p.price AS price, r.quantity AS quantity
            """, user_id=user_id)
            return [r.data() for r in res]

    @staticmethod
    def checkout(user_id):
        with driver.session() as s:
            s.run("""
                MATCH (u:User {id:$user_id})-[r:HAS_IN_CART]->(p:Product)
                WITH u, collect({id:p.id, name:p.name, quantity:r.quantity, price:p.price}) AS items
                CREATE (o:Order {id: randomUUID(), date: datetime(), total: reduce(t=0, i IN items | t + i.price * i.quantity)})
                CREATE (u)-[:PLACED_ORDER]->(o)
                FOREACH (item IN items |
                    MERGE (prod:Product {id:item.id})
                    CREATE (o)-[:CONTAINS]->(prod)
                )
                WITH u
                MATCH (u)-[r:HAS_IN_CART]->()
                DELETE r
            """, user_id=user_id)
        return {"status":"success", "message":"Order placed successfully"}


# ------------------------
# User History & Actions
# ------------------------
class History:
    @staticmethod
    def log_view(user_id, product_id):
        with driver.session() as s:
            s.run("""
                MERGE (u:User {id:$user_id})
                MERGE (p:Product {id:$product_id})
                CREATE (u)-[:VIEWED {time:datetime()}]->(p)
            """, user_id=user_id, product_id=product_id)

    @staticmethod
    def log_like(user_id, product_id):
        with driver.session() as s:
            s.run("""
                MERGE (u:User {id:$user_id})
                MERGE (p:Product {id:$product_id})
                MERGE (u)-[:LIKED]->(p)
            """, user_id=user_id, product_id=product_id)

    @staticmethod
    def add_to_wishlist(user_id, product_id):
        with driver.session() as s:
            s.run("""
                MERGE (u:User {id:$user_id})
                MERGE (p:Product {id:$product_id})
                MERGE (u)-[:WISHLISTED]->(p)
            """, user_id=user_id, product_id=product_id)

    @staticmethod
    def remove_from_wishlist(user_id, product_id):
        with driver.session() as s:
            s.run("""
                MATCH (u:User {id:$user_id})-[r:WISHLISTED]->(p:Product {id:$product_id})
                DELETE r
            """, user_id=user_id, product_id=product_id)

    @staticmethod
    def log_purchase(user_id, product_id):
        with driver.session() as s:
            s.run("""
                MERGE (u:User {id:$user_id})
                MERGE (p:Product {id:$product_id})
                CREATE (u)-[:PURCHASED {time:datetime()}]->(p)
            """, user_id=user_id, product_id=product_id)

    @staticmethod
    def log_return(user_id, product_id):
        with driver.session() as s:
            s.run("""
                MATCH (u:User {id:$user_id})-[r:PURCHASED]->(p:Product {id:$product_id})
                CREATE (u)-[:RETURNED {time:datetime()}]->(p)
            """, user_id=user_id, product_id=product_id)

    @staticmethod
    def get_user_history(user_id):
        with driver.session() as s:
            res = s.run("""
                MATCH (u:User {id:$user_id})-[r]->(p:Product)
                RETURN type(r) AS action, p.id AS product_id, r.time AS time
                ORDER BY r.time DESC
            """, user_id=user_id)
            return [r.data() for r in res]


# ------------------------
# Recommendations
# ------------------------
class Recommendation:
    @staticmethod
    def recommend_products(user_id, limit=5):
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

    @staticmethod
    def item_based_recommendations(product_id, limit=5):
        with driver.session() as s:
            result = s.run("""
                MATCH (p:Product {id:$product_id})
                MATCH (p)-[:IN_CATEGORY]->(c:Category)<-[:IN_CATEGORY]-(rec:Product)
                WHERE rec.id <> $product_id
                RETURN rec.id AS id, rec.name AS name, rec.price AS price, rec.category AS category
                LIMIT $limit
            """, product_id=product_id, limit=limit)
            return [r.data() for r in result]

    @staticmethod
    def seasonal_promotions(season=None, limit=5):
        with driver.session() as s:
            result = s.run("""
                MATCH (p:Product)
                WHERE $season IS NULL OR p.season = $season OR p.promo = true
                RETURN p.id AS id, p.name AS name, p.price AS price, p.category AS category
                LIMIT $limit
            """, season=season, limit=limit)
            return [r.data() for r in result]

    @staticmethod
    def manual_adjustment():
        with driver.session() as s:
            result = s.run("""
                MATCH (p:Product)
                WHERE exists(p.weight) AND p.weight > 0
                RETURN p.id AS id, p.name AS name, p.price AS price, p.category AS category, p.weight AS weight
                ORDER BY p.weight DESC
            """)
            return [r.data() for r in result]


# ------------------------
# User segmentation
# ------------------------
class User:
    @staticmethod
    def get_user_segment(user_id):
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
