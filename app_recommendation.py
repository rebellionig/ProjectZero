from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j_conn import (
    get_user_segment,
    item_based_recommendations,
    seasonal_promotions,
    manual_adjustment
)

app = Flask(__name__)
CORS(app)

# Сегментация пользователя
@app.route("/user_segment/<user_id>", methods=["GET"])
def segment(user_id):
    seg = get_user_segment(user_id)
    return jsonify({"user_id": user_id, "segment": seg})

# Item-based рекомендации
@app.route("/recommend/item/<product_id>", methods=["GET"])
def item_recommend(product_id):
    recs = item_based_recommendations(product_id)
    return jsonify(recs)

# Сезонные / акционные рекомендации
@app.route("/recommend/seasonal", methods=["GET"])
def seasonal():
    season = request.args.get("season")  # например "winter", "summer"
    recs = seasonal_promotions(season)
    return jsonify(recs)

# Ручная корректировка
@app.route("/recommend/manual", methods=["GET"])
def manual():
    recs = manual_adjustment()
    return jsonify(recs)

if __name__ == "__main__":
    app.run(debug=True)
