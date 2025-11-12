from locust import HttpUser, task, between

class EcommerceUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_recommendations(self):
        self.client.get("/recommendations/user123?algo=user_based&limit=10")

    @task
    def search_products(self):
        self.client.get("/search?q=laptop&min_price=500&max_price=2000")
