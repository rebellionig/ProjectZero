from neo4j_conn import driver

class CollaborativeFiltering:
    def __init__(self):
        self.algorithms = ["user_based", "item_based"]  # поддержка нескольких алгоритмов
        self.current_algo = "user_based"

    def set_algorithm(self, algo_name):
        if algo_name in self.algorithms:
            self.current_algo = algo_name
        else:
            raise ValueError(f"Algorithm {algo_name} not supported")

    # ------------------------
    # Регулярное обновление матрицы предпочтений
    # ------------------------
    def update_preference_matrix(self):
        """
        Построение матрицы User × Product с учётом покупок и лайков
        Сохраняется в виде свойств или отдельного узла в Neo4j
        """
        with driver.session() as s:
            # пример: считать количество взаимодействий (лайки + покупки)
            s.run("""
                MATCH (u:User)-[r:PURCHASED|LIKED]->(p:Product)
                WITH u, p, count(r) AS score
                MERGE (u)-[pref:PREFERS]->(p)
                SET pref.score = score
            """)
        print("Preference matrix updated successfully.")

    # ------------------------
    # Выдача рекомендаций на основе выбранного алгоритма
    # ------------------------
    def recommend(self, user_id, limit=10):
        with driver.session() as s:
            if self.current_algo == "user_based":
                # user-based CF: похожие пользователи
                result = s.run("""
                    MATCH (u:User {id:$user_id})-[:PREFERS]->(p:Product)
                    WITH u, collect(p) AS user_products
                    MATCH (other:User)-[:PREFERS]->(p2:Product)
                    WHERE other <> u AND any(prod IN p2 WHERE prod IN user_products)
                    WITH p2 AS rec, count(*) AS score
                    RETURN rec.id AS id, rec.name AS name, rec.category AS category, rec.price AS price, score
                    ORDER BY score DESC
                    LIMIT $limit
                """, user_id=user_id, limit=limit)
            else:
                # item-based CF: похожие товары
                result = s.run("""
                    MATCH (u:User {id:$user_id})-[:PREFERS]->(p:Product)
                    MATCH (p)-[:IN_CATEGORY]->(c:Category)<-[:IN_CATEGORY]-(rec:Product)
                    WHERE NOT (u)-[:PREFERS]->(rec)
                    RETURN rec.id AS id, rec.name AS name, rec.category AS category, rec.price AS price, count(*) AS score
                    ORDER BY score DESC
                    LIMIT $limit
                """, user_id=user_id, limit=limit)
            return [r.data() for r in result]
