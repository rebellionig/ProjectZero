from cf_engine import CollaborativeFiltering

cf = CollaborativeFiltering()

# ------------------------
# Обновление матрицы предпочтений (Batch)
# ------------------------
@app.route("/cf/update_matrix", methods=["POST"])
def update_matrix():
    cf.update_preference_matrix()
    return {"message": "Preference matrix updated successfully."}

# ------------------------
# Выдача CF рекомендаций
# ------------------------
@app.route("/cf/recommend/<user_id>", methods=["GET"])
def cf_recommend(user_id):
    algo = request.args.get("algo", "user_based")
    cf.set_algorithm(algo)
    limit = int(request.args.get("limit", 10))
    recs = cf.recommend(user_id, limit)
    return jsonify(recs)
