from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "12345678"  # замени на свой пароль Neo4j

driver = GraphDatabase.driver(uri, auth=(user, password))

def add_to_cart(user_id, product_id, quantity):
    with driver.session() as session:
        session.run("""
            MERGE (u:User {id: $user_id})
            MERGE (p:Product {id: $product_id})
            MERGE (u)-[r:HAS_IN_CART]->(p)
            ON CREATE SET r.quantity = $quantity
            ON MATCH SET r.quantity = r.quantity + $quantity
        """, user_id=user_id, product_id=product_id, quantity=quantity)

def remove_from_cart(user_id, product_id):
    with driver.session() as session:
        session.run("""
            MATCH (u:User {id: $user_id})-[r:HAS_IN_CART]->(p:Product {id: $product_id})
            DELETE r
        """, user_id=user_id, product_id=product_id)

def get_cart(user_id):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {id: $user_id})-[r:HAS_IN_CART]->(p:Product)
            RETURN p.id AS id, p.name AS name, p.price AS price, r.quantity AS quantity
        """, user_id=user_id)
        return [record.data() for record in result]

def checkout(user_id):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {id: $user_id})-[r:HAS_IN_CART]->(p:Product)
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
        return {"status": "success", "message": "Order placed successfully"}
