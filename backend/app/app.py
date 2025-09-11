from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
import mysql.connector
import bcrypt, os, requests

# Flask load
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# MySQL DB config
db_config = {
  'host': os.getenv("DB_HOST"),
  'user': os.getenv("DB_USER"),
  'password': os.getenv("DB_PASSWORD"),
  'database': os.getenv("DB_NAME")
}

# auth routes
@app.route("/register", methods=['POST', 'GET'])
def register():
  if request.method == "POST":
    username = request.form["username"]
    email = request.form["email"]
    hashed_password = bcrypt.hashpw(request.form["password"].encode("utf-8"), bcrypt.gensalt())

    # insert into table
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user (username, email, pass_hash)
        VALUES (%s, %s, %s)
    """, (username, email, hashed_password))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("app.login"))
  return render_template("register.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
  if request.method == "POST":
    username = request.form["username"]
    #password = request.form["password"]

    # check in table
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
      SELECT * FROM user WHERE username = %s
    """, (username))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    # return user on pass chk
    if user and bcrypt.checkpw(request.form["password"].encode("utf-8"), user["pass_hash"].encode("utf-8")):
      session["user_id"] = user["user_id"]
      session["username"] = user["username"]
      return redirect(url_for("app.search"))
    else:
      return "Please enter a valid username & password YB"
  return render_template("login.html")

@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("app.login"))

# search route
@app.route("/", methods=["POST", "GET"])
def search():
  result, message, in_inv_flag = None, None, False

  if request.method == "POST":
    card_name = request.form["card_name"]

    # check card if in table
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    try:
      cursor.execute("""
        SELECT * FROM card WHERE name LIKE %s
      """, ('%' + card_name + '%'))
      results = cursor.fetchall()
      result = results[0] if results else None

      # return result or pull on empty card
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

        # on successful response
        if response.status_code == 200:
          card_data = response.json()
          set_name = card_data['set_name']
          release_date = card_data['released_at']

          # check for existing set
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

          # add card
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

          # re-check on inserted card
          cursor.execute("""
            SELECT * FROM card WHERE name LIKE %s
          """, (card_data['name']))
          result = cursor.fetchone()
          message = "magic_url - card found"
        else:
          message = "magic_url - card not found"
    finally:
      cursor.close()
      conn.close()
  return render_template("search.html", result=result, message=message, in_inv_flag=in_inv_flag)

# inventory routes
@app.route("/add", methods=["POST"])
def add_to_inventory():
  card_id = request.form.get("card_id")
  condition = request.form.get("condition", "Near Mint")
  user_id = session.get("user_id", 1)

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