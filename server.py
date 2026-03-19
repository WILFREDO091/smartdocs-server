"""
SmartDocs Server - Servidor central para ANNAR DIAGNOSTICA
Ejecutar: python server.py
Requiere: pip install flask flask-cors
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# USUARIOS ADMIN
# ─────────────────────────────────────────────
ADMIN_USERS = {
    "wilfredo":       "clave-wilfredo-2024",
    "especialista1":  "clave-especialista1-2024",
    "especialista2":  "clave-especialista2-2024",
    "especialista3":  "clave-especialista3-2024",
    "especialista4":  "clave-especialista4-2024",
    "especialista5":  "clave-especialista5-2024",
    "supervisor":     "clave-supervisor-2024",
}

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def check_auth():
    username = request.headers.get("X-Username", "")
    api_key  = request.headers.get("X-API-Key", "")
    if username in ADMIN_USERS and ADMIN_USERS[username] == api_key:
        return username
    return None

def get_models_index():
    path = os.path.join(DATA_DIR, "models_index.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_models_index(index):
    path = os.path.join(DATA_DIR, "models_index.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# ENDPOINTS PÚBLICOS
# ─────────────────────────────────────────────

@app.route("/", methods=["GET"])
def home():
    return jsonify({"app": "SmartDocs Server - ANNAR DIAGNOSTICA", "status": "running", "version": "2.0"})

@app.route("/models", methods=["GET"])
def list_models():
    index = get_models_index()
    return jsonify({"models": index, "total": len(index)})

@app.route("/models/<model_id>", methods=["GET"])
def get_model(model_id):
    path = os.path.join(DATA_DIR, f"{model_id}.json")
    if not os.path.exists(path):
        return jsonify({"error": f"Modelo '{model_id}' no encontrado"}), 404
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/models/<model_id>/<section>", methods=["GET"])
def get_model_section(model_id, section):
    path = os.path.join(DATA_DIR, f"{model_id}.json")
    if not os.path.exists(path):
        return jsonify({"error": f"Modelo '{model_id}' no encontrado"}), 404
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if section not in data:
        return jsonify({"error": f"Sección '{section}' no existe"}), 404
    return jsonify(data[section])

# ─────────────────────────────────────────────
# ENDPOINTS ADMIN
# ─────────────────────────────────────────────

@app.route("/admin/upload-model", methods=["POST"])
def upload_model():
    user = check_auth()
    if not user:
        return jsonify({"error": "No autorizado. Verifica usuario y clave."}), 401

    body = request.get_json()
    if not body:
        return jsonify({"error": "Body JSON requerido"}), 400

    model_id        = body.get("model_id", "").strip().lower().replace(" ", "_")
    model_name      = body.get("model_name", model_id)
    description     = body.get("description", "")
    photoBaseUrl    = body.get("photoBaseUrl", None)
    pdfBaseUrl      = body.get("pdfBaseUrl", None)
    pdfManualUrl    = body.get("pdfManualUrl", None)
    pdfBulletinsUrl = body.get("pdfBulletinsUrl", None)
    pdfNotesUrl     = body.get("pdfNotesUrl", None)
    data            = body.get("data", {})

    if not model_id:
        return jsonify({"error": "model_id es requerido"}), 400

    model_data = {
        "model_id":        model_id,
        "model_name":      model_name,
        "description":     description,
        "photoBaseUrl":    photoBaseUrl,
        "pdfBaseUrl":      pdfBaseUrl,
        "pdfManualUrl":    pdfManualUrl,
        "pdfBulletinsUrl": pdfBulletinsUrl,
        "pdfNotesUrl":     pdfNotesUrl,
        "uploaded_by":     user,
        "uploaded_at":     datetime.now().isoformat(),
        **data
    }

    path = os.path.join(DATA_DIR, f"{model_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(model_data, f, ensure_ascii=False, indent=2)

    index = get_models_index()
    existing = next((m for m in index if m["model_id"] == model_id), None)
    entry = {
        "model_id":    model_id,
        "model_name":  model_name,
        "description": description,
        "uploaded_by": user,
        "last_updated": datetime.now().isoformat(),
        "sections": list(data.keys())
    }
    if existing:
        index[index.index(existing)] = entry
    else:
        index.append(entry)
    save_models_index(index)

    return jsonify({
        "success":     True,
        "message":     f"Modelo '{model_name}' guardado correctamente",
        "uploaded_by": user,
        "model_id":    model_id
    })


@app.route("/admin/upload-section", methods=["POST"])
def upload_section():
    user = check_auth()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    body     = request.get_json()
    model_id = body.get("model_id", "").strip().lower()
    section  = body.get("section", "").strip()
    data     = body.get("data")

    if not all([model_id, section, data is not None]):
        return jsonify({"error": "model_id, section y data son requeridos"}), 400

    path = os.path.join(DATA_DIR, f"{model_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            model_data = json.load(f)
    else:
        model_data = {"model_id": model_id}

    model_data[section]            = data
    model_data["last_updated"]     = datetime.now().isoformat()
    model_data["last_updated_by"]  = user

    with open(path, "w", encoding="utf-8") as f:
        json.dump(model_data, f, ensure_ascii=False, indent=2)

    index = get_models_index()
    entry = next((m for m in index if m["model_id"] == model_id), None)
    if entry:
        if section not in entry.get("sections", []):
            entry.setdefault("sections", []).append(section)
        entry["last_updated"] = model_data["last_updated"]
        save_models_index(index)

    return jsonify({
        "success":    True,
        "message":    f"Sección '{section}' del modelo '{model_id}' actualizada",
        "updated_by": user
    })


@app.route("/admin/delete-model/<model_id>", methods=["DELETE"])
def delete_model(model_id):
    user = check_auth()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    path = os.path.join(DATA_DIR, f"{model_id}.json")
    if not os.path.exists(path):
        return jsonify({"error": "Modelo no encontrado"}), 404

    os.remove(path)
    index = [m for m in get_models_index() if m["model_id"] != model_id]
    save_models_index(index)

    return jsonify({"success": True, "message": f"Modelo '{model_id}' eliminado por {user}"})


@app.route("/admin/users", methods=["GET"])
def list_users():
    user = check_auth()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    return jsonify({"users": list(ADMIN_USERS.keys()), "total": len(ADMIN_USERS)})


@app.route("/admin/verify", methods=["GET"])
def verify_credentials():
    user = check_auth()
    if not user:
        return jsonify({"valid": False}), 401
    return jsonify({"valid": True, "username": user})


# ─────────────────────────────────────────────
# INICIO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n{'='*50}")
    print(f"  SmartDocs Server - ANNAR DIAGNOSTICA")
    print(f"  Corriendo en http://localhost:{port}")
    print(f"  Usuarios admin configurados: {len(ADMIN_USERS)}")
    print(f"{'='*50}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
