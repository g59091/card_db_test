import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
import mysql.connector
from flask_cors import CORS, cross_origin
import bcrypt, os, requests, json

# Flask load
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# allow all origins (good for dev)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

CORS(app)

# app.config['CORS_HEADERS'] = "Content-Type"

# MySQL DB config
# db_config = {
#   'host': os.getenv("DB_HOST"),
#   'user': os.getenv("DB_USER"),
#   'password': os.getenv("DB_PASSWORD"),
#   'database': os.getenv("DB_NAME")
# }


cred = credentials.Certificate(
  json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT"))
)
firebase_admin.initialize_app(cred)

db = firestore.client()

# auth routes
@app.route("/register", methods=['POST', 'GET'])
def register():
  if request.method == "POST":
    username = request.form["username"]
    email = request.form["email"]
    hashed_password = bcrypt.hashpw(request.form["password"].encode("utf-8"), bcrypt.gensalt())
    print(username,email,hashed_password)

    # Goal: Migrate to using Users Colection
    # For each UserID create Inventory Collection /w Card Details
    # Note : Unique random ID
    sign_up_ref =  db.collection("Users").document(username).collection("Details").document("SignUpDetails")

    sign_up_ref.set({
      "Email": email,
      "PassHash": hashed_password,
      "Username": username
    })

    # conn = mysql.connector.connect(**db_config)
    # cursor = conn.cursor()
    # cursor.execute("""
    #     INSERT INTO user (username, email, pass_hash)
    #     VALUES (%s, %s, %s)
    # """, (username, email, hashed_password))
    # conn.commit()
    # cursor.close()
    # conn.close()

    return redirect(url_for("app.login"))
  return render_template("register.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
  if request.method == "POST":
    username = request.form["username"]
    #password = request.form["password"]

    # Goal: Migrate to Using Users Collection
    # Check across each UserID find the Details Collection
    # Check Users info
    # conn = mysql.connector.connect(**db_config)
    # cursor = conn.cursor(dictionary=True)
    # cursor.execute("""
    #   SELECT * FROM user WHERE username = %s
    # """, (username))
    # user = cursor.fetchone()
    # cursor.close()
    # conn.close()
    sign_up_ref =  db.collection("Users").document(username).collection("Details").document("SignUpDetails")
    user = sign_up_ref.get()

    # return user on pass chk
    # Change : consolidating user_id with username
    if user.exists and bcrypt.checkpw(request.form["password"].encode("utf-8"), user["PassHash"].encode("utf-8")):
     # session["user_id"] = user["user_id"]
      session["username"] = user["Username"]
      return redirect(url_for("app.search"))
    else:
      return "Please enter a valid username & password YB"
  return render_template("login.html")

@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("app.login"))

# search route
@app.route("/search", methods=["POST", "GET"])
@cross_origin()
def search():
  result, message, in_inv_flag = None, None, False

  if request.method == "POST":
    data = request.get_json()
    card_name = data.get("card_name")
    print(card_name)

    # Goal:Try searching through Users Collection 
    # Check Inventory Collection if Card is present
    # conn = mysql.connector.connect(**db_config)
    # cursor = conn.cursor(dictionary=True)
    # try:
    # cursor.execute("""
    #   SELECT * FROM card WHERE name LIKE %s
    # """, ('%' + card_name + '%'))
    # results = cursor.fetchall()
    # result = results[0] if results else None
    inv_ref =  db.collection("Users").document(session["username"]).collection("Inventory")
    cards = inv_ref.where("CardName", "==", card_name).get()

    # Adjust: Approach searching for Card inside of Inventory
    if result:
      card_id = result['card_id']
      user_id = session.get("user_id", 1)
      cursor.execute("""
        SELECT * FROM usercardinventory
        WHERE user_id = %s AND card_id = %s
      """, (user_id, card_id))
      in_inv_flag = cursor.fetchone() is not None
    else:
      magic_url = f"https://api.scryfall.com/cards/named?fuzzy={card_name}"
      response = requests.get(magic_url)
      print(response)
      # on successful response
      if response.status_code == 200:
        card_data = response.json()
        set_name = card_data['set_name']
        release_date = card_data['released_at']

        # Adjust: Consider removing these executes
        cursor.execute("""
          SELECT set_id FROM cardset WHERE name = %s
        """, (set_name))
        set_row = cursor.fetchone()

        if set_row:
          set_id = set_row['set_id']
        else:
          cursor.execute("""
            INSERT INTO cardset (name, release_date) VALUES (%s, %s)
          """, (set_name, release_date))
          conn.commit()
          set_id = cursor.lastrowid

        # Goal: Refactor to add Card Details and Inventory
        cursor.execute("""
          INSERT INTO card (name, type, rarity, mana_cost, rules_text, image_url, set_id)
          VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
          card_data['name'],
          card_data['type_line'],
          card_data['rarity'].capitalize(),
          card_data.get('mana_cost', ''),
          card_data.get('oracle_text', ''),
          card_data['image_uris']['normal'],
          set_id
        ))
        conn.commit()

        # Adjust: Consider removing this execute
        cursor.execute("""
          SELECT * FROM card WHERE name LIKE %s
        """, (card_data['name']))
        result = cursor.fetchone()
        message = "magic_url - card found"
      else:
        message = "magic_url - card not found"
    # finally:
    #   cursor.close()
    #   conn.close()
  # return render_template("search.html", result=result, message=message, in_inv_flag=in_inv_flag)
  return {"result" :result, "message":message, "in_inv_flag":in_inv_flag}

# inventory routes
@app.route("/add", methods=["POST"])
def add_to_inventory():
  card_id = request.form.get("card_id")
  condition = request.form.get("condition", "Near Mint")
  user_id = session.get("user_id", 1)

  # Adjust: Consider Removing these executes
  # Consider if we need extra FireBase master card list 
  conn = mysql.connector.connect(**db_config)
  cursor = conn.cursor()
  try:
    cursor.execute("""
      SELECT inventory_id, quantity FROM usercardinventory
      WHERE user_id = %s AND card_id = %s
    """, (user_id, card_id))
    card_in_inv = cursor.fetchone()

    if card_in_inv:
      cursor.execute("""
        UPDATE usercardinventory SET quantity = quantity + 1 WHERE inventory_id = %s
      """, (card_in_inv[0],))
    else:
      cursor.execute("""
        INSERT INTO usercardinventory (user_id, card_id, quantity, card_condition)
        VALUES (%s, %s, %s, %s)
      """, (user_id, card_id, 1, condition))
      
    conn.commit()
  finally:
    cursor.close()
    conn.close()
  return redirect(url_for("app.search"))

# Adjust: Consider Removing these executes
# Consider if we need extra FireBase master card list 
@app.route("/remove", methods=["POST"])
def remove_from_inventory():
  card_id = request.form.get("card_id")
  user_id = session.get("user_id", 1)

  conn = mysql.connector.connect(**db_config)
  cursor = conn.cursor()
  try:
    cursor.execute("""
      SELECT inventory_id, quantity FROM usercardinventory
      WHERE user_id = %s AND card_id = %s
    """, (user_id, card_id))
    card_in_inv = cursor.fetchone()

    # remove card
    if card_in_inv:
      inventory_id, qty = card_in_inv
      if qty > 1:
        cursor.execute("""
          UPDATE usercardinventory SET quantity = %s WHERE inventory_id = %s
        """, (qty - 1, inventory_id))
      else:
        cursor.execute("""
          DELETE FROM usercardinventory WHERE inventory_id = %s
        """, (inventory_id))
      conn.commit()
  finally:
    cursor.close()
    conn.close()
  return redirect(url_for("app.search"))

@app.route("/inventory")
def view_inventory():
  if "user_id" not in session:
    # "Unathorized. Please login."
    return redirect(url_for("app.login"))
  user_id = session["user_id"]

# Adjust: Refactor to view Card Details from Inventory
  conn = mysql.connector.connect(**db_config)
  cursor = conn.cursor(dictionary=True)
  try:
    cursor.execute("""
      SELECT c.name, c.image_url, i.quantity, i.card_condition
      FROM usercardinventory i
      JOIN card c ON i.card_id = c.card_id
      WHERE i.user_id = %s
    """, (user_id,))
    inventory = cursor.fetchall()
  finally:
    cursor.close()
    conn.close()
  return render_template("inventory.html", inventory=inventory)

# Start with flask web app, with debug as True,
# only if this is the starting page
if __name__ == '__main__':
    app.run(debug=True)