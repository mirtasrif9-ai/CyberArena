import os
import joblib
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from behavior_auth import train_admin_model, verify_admin_behavior, admin_model_exists

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"

ML_MODEL_PATH = os.path.join("ml_models", "ml_defense.joblib")

ml_bundle = None
ml_vectorizer = None
ml_model = None

# Adaptive memory: block same successful attack next time (exact match)
learned_blocks = set()

# Temporary storage for registered admins
# Later you can move this to SQLite
registered_admins = {
    "admin": {
        "password_hash": generate_password_hash("password123")
    }
}


def load_ml_defense():
    global ml_bundle, ml_vectorizer, ml_model
    if os.path.exists(ML_MODEL_PATH):
        ml_bundle = joblib.load(ML_MODEL_PATH)
        ml_vectorizer = ml_bundle["vectorizer"]
        ml_model = ml_bundle["model"]
        return True
    return False


load_ml_defense()

user_score = 0
system_score = 0


@app.route("/admin")
def admin_panel():
    if not session.get("admin_logged_in"):
        return redirect(url_for("module1"))
    return render_template("admin.html")


@app.route("/module1")
def module1():
    return render_template("module1.html")


@app.route("/module1/attack", methods=["POST"])
def attack():
    global user_score, system_score

    data = request.json
    username_input = data.get("username", "")
    password_input = data.get("password", "")

    combined_input = username_input + " " + password_input
    combined_lower = combined_input.lower()

    # ----------------------------
    # 1️⃣ Detection Layer
    # ----------------------------
    suspicious_patterns = [
        "drop",
        "union",
        "--",
        ";",
        "<script>"
    ]

    if any(pattern in combined_lower for pattern in suspicious_patterns):
        system_score += 10
        return jsonify({
            "result": "Blocked by AI ❌",
            "user_score": user_score,
            "system_score": system_score
        })

    # ----------------------------
    # 2️⃣ Simulated TRUE Evaluator
    # ----------------------------
    def evaluates_true(text):
        test = text.replace(" ", "").lower()
        if "or" in test and "=" in test:
            try:
                condition = test.split("or")[1]
                left, right = condition.split("=")
                if left.strip("'\"") == right.strip("'\""):
                    return True
            except:
                return False
        return False

    if evaluates_true(username_input) or evaluates_true(password_input):
        user_score += 10
        session["admin_reward_unlocked"] = True
        return jsonify({
            "result": "SQL Injection Successful ✅ (+10)",
            "reward": {
                "username": "CyberArena", "password": "cyber1098"
            },
            "user_score": user_score,
            "system_score": system_score
        })

    # ----------------------------
    # 3️⃣ Normal Login
    # ----------------------------
    real_username = "nUser"
    real_password = "nPass123"

    if username_input == real_username and password_input == real_password:
        session["admin_reward_unlocked"] = True
        return jsonify({
            "result": "Normal Login ℹ️",
            "reward": {
                "username": "CyberArena", "password": "cyber1098"
            },
            "user_score": user_score,
            "system_score": system_score
        })

    # ----------------------------
    # 4️⃣ Invalid
    # ----------------------------
    return jsonify({
        "result": "Invalid Credentials ❌",
        "user_score": user_score,
        "system_score": system_score
    })


@app.route("/module1-ml")
def module1_ml():
    if ml_model is None:
        return "ML model not found. Run: python train_ml_defense.py", 500
    return render_template("module1_ml.html")


@app.route("/module1-ml/attack", methods=["POST"])
def attack_ml():
    global user_score, system_score, ml_model

    if ml_model is None:
        return jsonify({
            "result": "ML model not loaded ❌",
            "user_score": user_score,
            "system_score": system_score
        }), 500

    data = request.json
    username_input = data.get("username", "")
    password_input = data.get("password", "")

    combined_input = f"{username_input} {password_input}"
    combined_lower = combined_input.lower()

    # ----------------------------
    # ML Defense Layer
    # ----------------------------
    if combined_lower in learned_blocks:
        system_score += 10
        return jsonify({
            "result": "Blocked by ML Defense (learned) ❌",
            "user_score": user_score,
            "system_score": system_score
        })

    X = ml_vectorizer.transform([combined_input])
    pred = int(ml_model.predict(X)[0])  # 1=malicious, 0=benign

    if pred == 1:
        system_score += 10
        return jsonify({
            "result": "Blocked by ML Defense ❌",
            "user_score": user_score,
            "system_score": system_score
        })

    # ----------------------------
    # Same login/attack logic as Module 1
    # ----------------------------
    def evaluates_true(text):
        test = text.replace(" ", "").lower()
        if "or" in test and "=" in test:
            try:
                condition = test.split("or", 1)[1]
                left, right = condition.split("=", 1)
                if left.strip("'\"") == right.strip("'\""):
                    return True
            except:
                return False
        return False

    real_username = "mlUser"
    real_password = "mlPass123"

    if evaluates_true(username_input) or evaluates_true(password_input):
        user_score += 10

        learned_blocks.add(combined_lower)

        X_new = ml_vectorizer.transform([combined_input])
        ml_model.partial_fit(X_new, [1])

        return jsonify({
            "result": "SQL Injection Successful ✅ (+10)",
            "reward": {"username": "CyberArena", "password": "cyber1098"},
            "user_score": user_score,
            "system_score": system_score
        })

    if username_input == real_username and password_input == real_password:
        return jsonify({
            "result": "Normal Login ℹ️",
            "reward": {"username": "CyberArena", "password": "cyber1098"},
            "user_score": user_score,
            "system_score": system_score
        })

    return jsonify({
        "result": "Invalid Credentials ❌",
        "user_score": user_score,
        "system_score": system_score
    })


@app.route("/admin-auth")
def admin_auth_page():
    if not session.get("admin_reward_unlocked"):
        return redirect(url_for("module1"))
    return render_template("admin_auth.html")


@app.route("/register-admin", methods=["POST"])
def register_admin():
    global registered_admins

    if not session.get("admin_logged_in"):
        return jsonify({
            "status": "failed",
            "message": "Unauthorized access."
        }), 403

    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    samples = data.get("samples", [])

    if not username or not password:
        return jsonify({
            "status": "failed",
            "message": "Username and password are required."
        }), 400

    if len(samples) < 5:
        return jsonify({
            "status": "failed",
            "message": "At least 5 typing samples are required."
        }), 400

    if username in registered_admins:
        return jsonify({
            "status": "failed",
            "message": "Username already exists."
        }), 400

    try:
        # Train the keystroke behavior model
        train_admin_model(username, samples)

        # Store hashed password
        registered_admins[username] = {
            "password_hash": generate_password_hash(password)
        }

        return jsonify({
            "status": "success",
            "message": f"Admin '{username}' registered successfully."
        })

    except Exception as e:
        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500


@app.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    behavior_sample = data.get("behavior_sample")

    admin_data = registered_admins.get(username)

    if not admin_data:
        return jsonify({
            "status": "failed",
            "message": "User not found"
        }), 404

    # Check password first
    if not check_password_hash(admin_data["password_hash"], password):
        return jsonify({
            "status": "failed",
            "message": "Invalid credentials"
        }), 401

    # If this user has a trained behavior model, behavior is mandatory
    if admin_model_exists(username):
        if not behavior_sample:
            return jsonify({
                "status": "failed",
                "message": "Behavior sample required"
            }), 400

        matched, message = verify_admin_behavior(username, behavior_sample)
        if not matched:
            return jsonify({
                "status": "failed",
                "message": message
            }), 401

    session["admin_logged_in"] = True
    session["logged_in_admin"] = username
    session.pop("admin_reward_unlocked", None)

    return jsonify({
        "status": "success",
        "message": "Login successful"
    })


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    session.pop("logged_in_admin", None)
    return redirect(url_for("module1"))


if __name__ == "__main__":
    app.run(debug=True)