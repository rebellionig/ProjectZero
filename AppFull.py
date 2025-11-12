from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from neo4j_conn import (
    get_driver, Cart, History, Recommendation, User,
    driver, log_view, log_like, add_to_wishlist, remove_from_wishlist,
    log_purchase, log_return, get_user_history, recommend_products,
    recommend_products_advanced, get_user_segment, item_based_recommendations,
    seasonal_promotions, manual_adjustment, add_to_cart, remove_from_cart, get_cart, checkout
)
from cf_engine import CollaborativeFiltering
from utils import hash_password, verify_password, create_access_token, decode_token
import os, uuid, datetime, pyotp
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# Mail configuration
app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 25)),
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=False,
)
mail = Mail(app)

# Neo4j driver & CF engine
driver = get_driver()
cf = CollaborativeFiltering()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# ------------------------
# USERS
# ------------------------
def create_user_in_db(email, password, full_name, phone=None):
    user_id = str(uuid.uuid4())
    hashed = hash_password(password)
    created_at = datetime.datetime.utcnow().isoformat()
    with driver.session() as session:
        session.execute_write(lambda tx: tx.run(
            """
            CREATE (u:User {user_id:$user_id, email:$email, password:$password, full_name:$full_name,
                            phone:$phone, created_at:$created_at, is_verified:false, twofa_enabled:false, privacy:'public'})
            WITH u
            MERGE (r:Role {name:'user'})
            CREATE (u)-[:HAS_ROLE]->(r)
            RETURN u
            """,
            user_id=user_id, email=email, password=hashed, full_name=full_name, phone=phone, created_at=created_at
        ))
    return user_id

def get_user_by_email(email):
    with driver.session() as session:
        res = session.execute_read(lambda tx: tx.run("MATCH (u:User {email:$email}) RETURN u", email=email).single())
        return res["u"] if res else None

def create_login_history(user_id, ip, success=True):
    with driver.session() as session:
        session.execute_write(lambda tx: tx.run(
            """
            MATCH (u:User {user_id:$user_id})
            CREATE (u)-[:LOGIN_EVENT {time:$time, ip:$ip, success:$success}]->(:Event)
            """,
            user_id=user_id, time=datetime.datetime.utcnow().isoformat(), ip=ip, success=success
        ))

@app.route("/api/register", methods=["POST"])
@limiter.limit("10 per minute")
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name", "")
    phone = data.get("phone")
    if get_user_by_email(email):
        return jsonify({"error":"user_exists"}), 400
    user_id = create_user_in_db(email, password, full_name, phone)
    token = create_access_token(user_id, extra={"action":"verify_email"}, minutes=60*24)
    verify_link = f"{FRONTEND_URL}/verify-email?token={token}"
    try:
        msg = Message(subject="Verify your account", recipients=[email], body=f"Please click {verify_link}")
        mail.send(msg)
    except Exception as e:
        app.logger.warning("Mail send failed: %s", e)
    return jsonify({"msg":"registered", "user_id":user_id}), 201

@app.route("/api/verify-email", methods=["POST"])
def verify_email():
    token = request.json.get("token")
    payload = decode_token(token)
    if not payload or payload.get("action")!="verify_email":
        return jsonify({"error":"invalid_token"}), 400
    user_id = payload.get("sub")
    with driver.session() as session:
        session.execute_write(lambda tx: tx.run("MATCH (u:User {user_id:$user_id}) SET u.is_verified = true RETURN u", user_id=user_id))
    return jsonify({"msg":"verified"})

@app.route("/api/login", methods=["POST"])
@limiter.limit("20 per minute")
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    user_record = get_user_by_email(email)
    if not user_record:
        return jsonify({"error":"invalid_credentials"}), 401
    user = dict(user_record)
    if not verify_password(password, user["password"]):
        create_login_history(user["user_id"], request.remote_addr, success=False)
        return jsonify({"error":"invalid_credentials"}), 401
    if user.get("twofa_enabled", False):
        temp = create_access_token(user["user_id"], extra={"action":"2fa"}, minutes=5)
        return jsonify({"twofa_required": True, "token": temp}), 200
    access = create_access_token(user["user_id"], extra={"roles": ["user"]})
    create_login_history(user["user_id"], request.remote_addr, success=True)
    return jsonify({"access_token": access})

@app.route("/api/verify-2fa", methods=["POST"])
def verify_2fa():
    token = request.json.get("token")
    code = request.json.get("code")
    payload = decode_token(token)
    if not payload or payload.get("action")!="2fa":
        return jsonify({"error":"invalid_token"}), 400
    user_id = payload.get("sub")
    with driver.session() as session:
        res = session.execute_read(lambda tx: tx.run("MATCH (u:User {user_id:$user_id}) RETURN u.twofa_secret as s, u.is_verified as v", user_id=user_id).single())
        if not res:
            return jsonify({"error":"user_not_found"}), 404
        s = res["s"]
    if not s:
        return jsonify({"error":"2fa_not_setup"}), 400
    totp = pyotp.TOTP(s)
    if not totp.verify(code):
        create_login_history(user_id, request.remote_addr, success=False)
        return jsonify({"error":"invalid_2fa"}), 401
    access = create_access_token(user_id, extra={"roles":["user"]})
    create_login_history(user_id, request.remote_addr, success=True)
    return jsonify({"access_token": access})

@app.route("/api/setup-2fa", methods=["POST"])
def setup_2fa():
    header = request.headers.get("Authorization","")
    token = header.replace("Bearer ","")
    payload = decode_token(token)
    if not payload:
        return jsonify({"error":"not_authenticated"}), 401
    user_id = payload.get("sub")
    secret = pyotp.random_base32()
    uri = pyotp.TOTP(secret).provisioning_uri(name=f"user-{user_id}", issuer_name="MyShop")
    with driver.session() as session:
        session.execute_write(lambda tx: tx.run("MATCH (u:User {user_id:$user_id}) SET u.twofa_secret=$secret, u.twofa_enabled=true RETURN u", user_id=user_id, secret=secret))
    return jsonify({"otp_uri": uri, "secret": secret})

@app.route("/api/request-reset", methods=["POST"])
def request_reset():
    email = request.json.get("email")
    user = get_user_by_email(email)
    if not user:
        return jsonify({"msg":"ok"})
    user_id = dict(user)["user_id"]
    token = create_access_token(user_id, extra={"action":"reset_password"}, minutes=60)
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    try:
        msg = Message(subject="Password reset", recipients=[email], body=f"Reset: {reset_link}")
        mail.send(msg)
    except Exception as e:
        app.logger.warning("Mail send failed: %s", e)
    return jsonify({"msg":"ok"})

@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    token = request.json.get("token")
    newpass = request.json.get("new_password")
    payload = decode_token(token)
    if not payload or payload.get("action")!="reset_password":
        return jsonify({"error":"invalid_token"}), 400
    user_id = payload.get("sub")
    hashed = hash_password(newpass)
    with driver.session() as session:
        session.execute_write(lambda tx: tx.run("MATCH (u:User {user_id:$user_id}) SET u.password=$hashed RETURN u", user_id=user_id, hashed=hashed))
    return jsonify({"msg":"password_changed"})

@app.route("/api/profile", methods=["GET","PUT"])
def profile():
    header = request.headers.get("Authorization","")
    token = header.replace("Bearer ","")
    payload = decode_token(token)
    if not payload:
        return jsonify({"error":"not_authenticated"}), 401
    user_id = payload.get("sub")
    if request.method == "GET":
        with driver.session() as session:
            res = session.execute_read(lambda tx: tx.run("MATCH (u:User {user_id:$user_id}) RETURN u", user_id=user_id).single())
            if not res: return jsonify({"error":"not_found"}), 404
            u = dict(res["u"])
            u.pop("password", None)
            u.pop("twofa_secret", None)
            return jsonify(u)
    else:
        data = request.json
        qset = []
        params = {"user_id":user_id}
        if "full_name" in data:
            qset.append("u.full_name=$full_name"); params["full_name"]=data["full_name"]
        if "phone" in data:
            qset.append("u.phone=$phone"); params["phone"]=data["phone"]
        if "privacy" in data:
            qset.append("u.privacy=$privacy"); params["privacy"]=data["privacy"]
        set_clause = ", ".join(qset)
        with driver.session() as session:
            session.execute_write(lambda tx: tx.run(f"MATCH (u:User {{user_id:$user_id}}) SET {set_clause} RETURN u", **params))
        return jsonify({"msg":"updated"})


# ------------------------
# PRODUCTS
# ------------------------
@app.route("/products", methods=['POST'])
def create_product():
    data = request.json
    with driver.session() as session:
        session.run("""
            MERGE (c:Category {name: $category})
            CREATE (p:Product {
                id:$id, name:$name, category:$category,
                price:$price, brand:$brand,
                description:$description, sku:$sku,
                images:$images, tags:$tags, options:$options,
                createdAt: datetime()
            })
            MERGE (p)-[:BELONGS_TO]->(c)
        """, **data)
    return jsonify({"message": "Product created"}), 201

@app.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    with driver.session() as s:
        result = s.run("MATCH (p:Product {id:$id}) RETURN p", id=product_id)
        product = result.single()
        if product:
            return jsonify(product["p"])
        return jsonify({"error": "Product not found"}), 404

@app.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.json
    with driver.session() as s:
        s.run("""
            MATCH (p:Product {id:$id})
            SET p.name=$name, p.category=$category, p.price=$price, p.brand=$brand
        """, **data, id=product_id)
    return jsonify({"message": "Product updated"})

@app.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    with driver.session() as s:
        s.run("MATCH (p:Product {id:$id}) DETACH DELETE p", id=product_id)
    return jsonify({"message": "Product deleted"})


# ------------------------
# REVIEWS
# ------------------------
@app.route("/products/<sku>/review", methods=['POST'])
def add_review(sku):
    data = request.json
    with driver.session() as s:
        s.run("""
            MATCH (p:Product {sku:$sku})
            CREATE (r:Review {rating:$rating, comment:$comment, date:datetime()})
            CREATE (p)-[:HAS_REVIEW]->(r)
        """, sku=sku, rating=float(data.get("rating")), comment=data.get("comment",""))
    return jsonify({"message": "Review added"}), 201

@app.route("/products/<sku>/reviews", methods=['GET'])
def get_reviews(sku):
    with driver.session() as s:
        result = s.run("""
            MATCH (p:Product {sku:$sku})-[:HAS_REVIEW]->(r:Review)
            RETURN r.rating AS rating, r.comment AS comment, r.date AS date
        """, sku=sku)
        reviews = [dict(r) for r in result]
        avg_rating = sum(r["rating"] for r in reviews)/len(reviews) if reviews else 0
    return jsonify({"reviews": reviews, "average_rating": round(avg_rating,2)})

# ------------------------
# SEARCH
# ------------------------
@app.route("/search", methods=["GET"])
def search_products():
    q = request.args.get("q", "")
    category = request.args.get("category")
    brand = request.args.get("brand")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort_by", "name")

    query = "MATCH (p:Product) WHERE toLower(p.name) CONTAINS toLower($q)"
    if category: query += " AND toLower(p.category)=toLower($category)"
    if brand: query += " AND toLower(p.brand)=toLower($brand)"
    if min_price is not None: query += " AND p.price >= $min_price"
    if max_price is not None: query += " AND p.price <= $max_price"
    query += f" RETURN p.id AS id, p.name AS name, p.category AS category, p.brand AS brand, p.price AS price"
    if sort_by in ["price","name","rating"]: query += f" ORDER BY p.{sort_by} ASC"

    with driver.session() as s:
        result = s.run(query, q=q, category=category, brand=brand, min_price=min_price, max_price=max_price)
        return jsonify([r.data() for r in result])

@app.route("/search/fulltext", methods=["GET"])
def search_fulltext():
    q = request.args.get("q", "")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    if not q: return jsonify([])
    query = """
        CALL db.index.fulltext.queryNodes("productFullTextIndex",$q) YIELD node, score
        WHERE ($min_price IS NULL OR node.price>=$min_price)
          AND ($max_price IS NULL OR node.price<=$max_price)
        RETURN node.id AS id,node.name AS name,node.category AS category,node.brand AS brand,node.price AS price,score
        ORDER BY score DESC
    """
    with driver.session() as s:
        result = s.run(query, q=q, min_price=min_price, max_price=max_price)
        return jsonify([r.data() for r in result])


# ------------------------
# HISTORY / USER ACTIONS
# ------------------------
@app.route("/history/view", methods=["POST"])
def view_product():
    data = request.json
    log_view(data["user_id"], data["product_id"])
    return jsonify({"message":"View logged"})

@app.route("/history/like", methods=["POST"])
def like_product():
    data = request.json
    log_like(data["user_id"], data["product_id"])
    return jsonify({"message":"Product liked"})

@app.route("/history/wishlist/add", methods=["POST"])
def wishlist_add():
    data = request.json
    add_to_wishlist(data["user_id"], data["product_id"])
    return jsonify({"message":"Added to wishlist"})

@app.route("/history/wishlist/remove", methods=["POST"])
def wishlist_remove():
    data = request.json
    remove_from_wishlist(data["user_id"], data["product_id"])
    return jsonify({"message":"Removed from wishlist"})

@app.route("/history/purchase", methods=["POST"])
def purchase():
    data = request.json
    log_purchase(data["user_id"], data["product_id"])
    return jsonify({"message":"Purchase logged"})

@app.route("/history/return", methods=["POST"])
def return_item():
    data = request.json
    log_return(data["user_id"], data["product_id"])
    return jsonify({"message":"Return logged"})

@app.route("/history/<user_id>", methods=["GET"])
def get_history(user_id):
    return jsonify(get_user_history(user_id))

@app.route("/history/recommend/<user_id>", methods=["GET"])
def recommend_history(user_id):
    recs = recommend_products(user_id)
    return jsonify(recs)

@app.route("/history/recommend_advanced/<user_id>", methods=["GET"])
def recommend_advanced_history(user_id):
    recs = recommend_products_advanced(user_id)
    return jsonify(recs)


# ------------------------
# CART
# ------------------------
@app.route("/cart/add", methods=["POST"])
def add_to_cart_route():
    data = request.json
    add_to_cart(data["user_id"], data["product_id"], data["quantity"])
    return jsonify({"message":"Item added to cart"})

@app.route("/cart/remove", methods=["POST"])
def remove_from_cart_route():
    data = request.json
    remove_from_cart(data["user_id"], data["product_id"])
    return jsonify({"message":"Item removed from cart"})

@app.route("/cart/<user_id>", methods=["GET"])
def get_cart_route(user_id):
    return jsonify(get_cart(user_id))

@app.route("/cart/checkout", methods=["POST"])
def checkout_route():
    data = request.json
    res = checkout(data["user_id"])
    return jsonify(res)


# ------------------------
# RECOMMENDATIONS
# ------------------------
@app.route("/recommend/item_based/<user_id>", methods=["GET"])
def item_based(user_id):
    recs = item_based_recommendations(user_id)
    return jsonify(recs)

@app.route("/recommend/seasonal/<user_id>", methods=["GET"])
def seasonal(user_id):
    recs = seasonal_promotions(user_id)
    return jsonify(recs)

@app.route("/recommend/manual/<user_id>", methods=["GET"])
def manual(user_id):
    recs = manual_adjustment(user_id)
    return jsonify(recs)


# ------------------------
# ADMIN
# ------------------------
@app.route("/admin/set-role", methods=["POST"])
def set_role():
    data = request.json
    user_id = data["user_id"]
    role = data["role"]
    with driver.session() as s:
        s.run("MATCH (u:User {user_id:$user_id})-[:HAS_ROLE]->(r) SET r.name=$role RETURN r", user_id=user_id, role=role)
    return jsonify({"message":"Role updated"})


if __name__=="__main__":
    print("Starting full app with Neo4j")
    app.run(debug=True)
