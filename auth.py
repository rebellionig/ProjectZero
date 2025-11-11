# app.py (auth + API)
from flask import Flask, request, jsonify
from neo4j_conn import get_driver
from utils import hash_password, verify_password, create_access_token, decode_token
from flask_cors import CORS
from dotenv import load_dotenv
import os, uuid, datetime, pyotp
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message

load_dotenv()

app = Flask(__name__)
CORS(app)

# rate limiter
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# Mail (configure .env)
app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 25)),
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=False,
)
mail = Mail(app)

driver = get_driver()
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

def create_user_in_db(email, password, full_name, phone=None):
    user_id = str(uuid.uuid4())
    hashed = hash_password(password)
    created_at = datetime.datetime.utcnow().isoformat()
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(
                """
                CREATE (u:User {user_id:$user_id, email:$email, password:$password, full_name:$full_name,
                                phone:$phone, created_at:$created_at, is_verified:false, twofa_enabled:false, privacy:'public'})
                WITH u
                MERGE (r:Role {name:'user'})
                CREATE (u)-[:HAS_ROLE]->(r)
                RETURN u
                """,
                user_id=user_id, email=email, password=hashed, full_name=full_name, phone=phone, created_at=created_at
            )
        )
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
            """, user_id=user_id, time=datetime.datetime.utcnow().isoformat(), ip=ip, success=success
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
    # send verification email (simple token)
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
    # if 2FA enabled -> require 2FA step
    if user.get("twofa_enabled", False):
        # issue temporary token for 2fa verification
        temp = create_access_token(user["user_id"], extra={"action":"2fa"}, minutes=5)
        return jsonify({"twofa_required": True, "token": temp}), 200
    # else create access token
    access = create_access_token(user["user_id"], extra={"roles": ["user"]})
    create_login_history(user["user_id"], request.remote_addr, success=True)
    return jsonify({"access_token": access})

@app.route("/api/verify-2fa", methods=["POST"])
def verify_2fa():
    token = request.json.get("token")  # temp token with action=2fa
    code = request.json.get("code")
    payload = decode_token(token)
    if not payload or payload.get("action")!="2fa":
        return jsonify({"error":"invalid_token"}), 400
    user_id = payload.get("sub")
    # get user's secret
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
    # Auth required: we expect Authorization: Bearer <access_token>
    header = request.headers.get("Authorization","")
    token = header.replace("Bearer ","")
    payload = decode_token(token)
    if not payload:
        return jsonify({"error":"not_authenticated"}), 401
    user_id = payload.get("sub")
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=f"user-{user_id}", issuer_name="MyShop")
    # store secret in DB
    with driver.session() as session:
        session.execute_write(lambda tx: tx.run("MATCH (u:User {user_id:$user_id}) SET u.twofa_secret=$secret, u.twofa_enabled=true RETURN u", user_id=user_id, secret=secret))
    return jsonify({"otp_uri": uri, "secret": secret})

@app.route("/api/request-reset", methods=["POST"])
def request_reset():
    email = request.json.get("email")
    user = get_user_by_email(email)
    if not user:
        return jsonify({"msg":"ok"})  # don't leak
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
    # get or update profile
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
            # remove internal fields
            u.pop("password", None)
            u.pop("twofa_secret", None)
            return jsonify(u)
    else:
        data = request.json
        # allowed updates: full_name, phone, privacy
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

@app.route("/api/login-history", methods=["GET"])
def login_history():
    header = request.headers.get("Authorization","")
    token = header.replace("Bearer ","")
    payload = decode_token(token)
    if not payload:
        return jsonify({"error":"not_authenticated"}), 401
    user_id = payload.get("sub")
    with driver.session() as session:
        res = session.execute_read(lambda tx: tx.run(
            "MATCH (u:User {user_id:$user_id})-[e:LOGIN_EVENT]->(ev:Event) RETURN e.time as time, e.ip as ip, e.success as success ORDER BY e.time DESC LIMIT 50", user_id=user_id).data())
    return jsonify({"events": res})

# Admin route: change role
@app.route("/api/admin/set-role", methods=["POST"])
def set_role():
    header = request.headers.get("Authorization","")
    token = header.replace("Bearer ","")
    payload = decode_token(token)
    if not payload: return jsonify({"error":"not_authenticated"}), 401
    caller = payload.get("sub")
    # check caller has admin role
    with driver.session() as session:
        is_admin = session.execute_read(lambda tx: tx.run("MATCH (u:User {user_id:$id})-[:HAS_ROLE]->(r:Role {name:'admin'}) RETURN count(r)>0 as ok", id=caller).single())["ok"]
        if not is_admin: return jsonify({"error":"forbidden"}), 403
    data = request.json
    user_id = data.get("user_id")
    role = data.get("role")
    with driver.session() as session:
        session.execute_write(lambda tx: tx.run("MATCH (u:User {user_id:$user_id}) MERGE (r:Role {name:$role}) MERGE (u)-[:HAS_ROLE]->(r)", user_id=user_id, role=role))
    return jsonify({"msg":"role_set"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
