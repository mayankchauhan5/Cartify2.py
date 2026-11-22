from flask import (
    Flask, render_template_string, request,
    redirect, url_for, session, flash)
import sqlite3
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key="cartify_mca_project_secret_key"
DATABASE="cartify.db"

# Default admin credentials
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

#Database
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    db=get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT,
            stock INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            address TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    #payment columns to existing orders table
    order_columns=[row["name"] for row in
        db.execute("PRAGMA table_info(orders)").fetchall()]
    if "payment_method" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'COD'")
    if "payment_status" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'Pending'")
    if "transaction_id" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN transaction_id TEXT")

    db.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    """)
    count=db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count==0:
        products=[
            ("Wireless Headphones", "Electronics", 1499,
             "Enjoy clear sound with comfortable wireless headphones.",
             "🎧"),
            ("Smart Watch", "Electronics", 2199,
             "A stylish smartwatch for everyday use.",
             "⌚"),
            ("Laptop Backpack", "Accessories", 899,
             "A spacious backpack suitable for laptops and accessories.",
             "🎒"),
            ("Running Shoes", "Fashion", 1299,
             "Comfortable shoes for walking and running.",
             "👟"),
            ("Cotton T-Shirt", "Fashion", 499,
             "Casual cotton T-shirt for daily wear.",
             "👕"),
            ("Bluetooth Speaker", "Electronics", 999,
             "Portable speaker with quality sound.",
             "🔊"),
            ("Desk Lamp", "Home", 699,
             "Modern LED desk lamp for your study table.",
             "💡"),
            ("Coffee Mug", "Home", 299,
             "Simple and stylish coffee mug.",
             "☕"),]
        db.executemany("""INSERT INTO products (name, category, price, description, image, stock)
        VALUES (?, ?, ?, ?, ?, ?)""",[(name, category, price, description, image, 10)
        for name,category,price,description,image in products])
    db.commit()
    db.close()

#Authentication
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

#Website Design
BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} | Cartify</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, sans-serif;
            background: #f5f6fa;
            color: #222;
        }
        nav {
            background: #172554;
            color: white;
            padding: 17px 7%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        nav h2 {
            font-size: 27px;
            color: #facc15;
        }
        nav a {
            color: white;
            text-decoration: none;
            margin: 0 9px;
            font-size: 14px;
        }
        nav a:hover {
            color: #facc15;
        }
        .container {
            width: 86%;
            max-width: 1200px;
            margin: 35px auto;
            min-height: 65vh;
        }
        .hero {
            background: linear-gradient(120deg, #172554, #2563eb);
            color: white;
            padding: 65px 35px;
            border-radius: 15px;
            margin-bottom: 35px;
        }
        .hero h1 {
            font-size: 38px;
            margin-bottom: 15px;
        }
        .hero p {
            font-size: 17px;
            margin-bottom: 25px;
        }
        .btn {
            display: inline-block;
            background: #2563eb;
            color: white;
            padding: 11px 18px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            margin: 5px 3px;
            font-size: 14px;
        }
        .btn:hover {
            background: #1d4ed8;
        }
        .yellow {
            background: #facc15;
            color: #172554;
        }
        .yellow:hover {
            background: #eab308;
        }
        .red {
            background: #dc2626;
        }
        .green {
            background: #16a34a;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 22px;
            margin-top: 25px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 3px 12px #00000012;
        }
        .product-image {
            height: 140px;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #eff6ff;
            border-radius: 10px;
            font-size: 65px;
            margin-bottom: 15px;
        }
        .card h3 {
            margin-bottom: 10px;
        }
        .price {
            color: #2563eb;
            font-size: 21px;
            font-weight: bold;
            margin: 12px 0;
        }
        input, textarea, select {
            width: 100%;
            padding: 12px;
            margin: 9px 0 17px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 15px;
        }
        label {
            font-weight: bold;
        }
        .form-box {
            background: white;
            max-width: 480px;
            margin: 35px auto;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 3px 15px #00000012;
        }
        .form-box h2 {
            margin-bottom: 20px;
            text-align: center;
            color: #172554;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin: 20px 0;
        }
        th, td {
            padding: 14px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }
        th {
            background: #172554;
            color: white;
        }
        .message {
            padding: 13px;
            margin-bottom: 15px;
            background: #dcfce7;
            color: #166534;
            border-radius: 6px;
        }
        .error {
            background: #fee2e2;
            color: #991b1b;
        }
        .total {
            text-align: right;
            font-size: 23px;
            font-weight: bold;
            margin: 20px 0;
        }
        footer {
            background: #172554;
            color: white;
            text-align: center;
            padding: 25px;
            margin-top: 45px;
        }
        .search {
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }
        .search input {
            margin: 0;
        }
        @media(max-width: 600px) {
            .container {
                width: 94%;
            }
            nav {
                justify-content: center;
            }
            nav div {
                text-align: center;
            }
            .hero h1 {
                font-size: 28px;
            }
            table {
                font-size: 12px;
            }
            th, td {
                padding: 8px;
            }
        }
    </style>
</head>
<body>
<nav>
    <h2>🛒 Cartify</h2>
    <div>
        <a href="{{ url_for('home') }}">Home</a>
        <a href="{{ url_for('home') }}">Products</a>
        {% if session.get('user_id') %}
            <a href="{{ url_for('cart') }}">Cart</a>
            <a href="{{ url_for('my_orders') }}">My Orders</a>
            <a href="{{ url_for('logout') }}">Logout</a>
        {% elif session.get('admin') %}
            <a href="{{ url_for('admin_dashboard') }}">Dashboard</a>
            <a href="{{ url_for('admin_orders') }}">Orders</a>
            <a href="{{ url_for('admin_logout') }}">Logout</a>
        {% else %}
            <a href="{{ url_for('login') }}">Login</a>
            <a href="{{ url_for('register') }}">Register</a>
            <a href="{{ url_for('admin_login') }}">Admin</a>
        {% endif %}
    </div>
</nav>

<div class="container">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            <div class="message {{ 'error' if category == 'error' else '' }}">
                {{ message }}
            </div>
        {% endfor %}
    {% endwith %}
    {{ content | safe }}
</div>
<footer>
    <h3>Cartify - Online Shopping System</h3>
    <p>Simple • Convenient • Reliable Shopping</p>
    <p>© 2026 Cartify. MCA Minor Project.</p>
</footer>
</body>
</html>
"""
def render_page(title, content,**kwargs):
    body=render_template_string(content,**kwargs)
    return render_template_string(BASE,title=title,content=body)

#Home and Products
@app.route("/")
def home():
    db=get_db()
    search=request.args.get("search", "").strip()
    category=request.args.get("category", "").strip()
    sql="SELECT * FROM products WHERE 1=1"
    params=[]
    if search:
        sql+=" AND (name LIKE ? OR category LIKE ?)"
        params.extend(["%" + search + "%", "%" + search + "%"])
    if category:
        sql+=" AND category = ?"
        params.append(category)
    products=db.execute(sql, params).fetchall()
    categories=db.execute("SELECT DISTINCT category FROM products").fetchall()
    db.close()
    content="""
    <div class="hero">
        <h1>Welcome to Cartify!</h1>
        <p>Your one-stop destination for convenient online shopping.</p>
        <a href="#products" class="btn yellow">Shop Now</a>
    </div>
    <h2 id="products">Explore Our Products</h2>
    <form class="search" method="GET">
        <input type="text" name="search"
               placeholder="Search products..."
               value="{{ search }}">
        <button class="btn">Search</button>
    </form>
    <form method="GET">
        <label>Filter by Category:</label>
        <select name="category" onchange="this.form.submit()">
            <option value="">All Categories</option>
            {% for c in categories %}
            <option value="{{ c.category }}"
                {% if selected == c.category %}selected{% endif %}>
                {{ c.category }}
            </option>
            {% endfor %}
        </select>
    </form>
    <div class="grid">
        {% for p in products %}
        <div class="card">
            <div class="product-image">{{ p.image }}</div>
            <h3>{{ p.name }}</h3>
            <p>{{ p.category }}</p>
            <p class="price">₹{{ "%.2f"|format(p.price) }}</p>
            <a class="btn" href="{{ url_for('product_detail', product_id=p.id) }}">
                View Details
            </a>
        </div>
        {% else %}
        <p>No products found.</p>
        {% endfor %}
    </div>
    """
    return render_page("Home",content,products=products,categories=categories,
        search=search,selected=category)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db=get_db()
    product=db.execute("SELECT * FROM products WHERE id=?",(product_id,)).fetchone()
    db.close()

    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("home"))

    content="""
    <div class="card">
        <div class="product-image">{{ p.image }}</div>
        <h2>{{ p.name }}</h2>
        <p>Category: {{ p.category }}</p>
        <p>{{ p.description }}</p>
        <p class="price">₹{{ "%.2f"|format(p.price) }}</p>
        <p><b>Available Stock:</b> {{ p.stock }}</p>
        {% if p.stock > 0 %}
        <p style="color:green;">In Stock</p>
        {% else %}
        <p style="color:red;">Out of Stock</p>
        {% endif %}

        {% if p.stock > 0 %}
        <form method="POST" action="{{ url_for('add_to_cart',product_id=p.id) }}">
        <label>Quantity:</label>
        <input type="number" name="quantity" value="1" min="1" max="{{ p.stock }}" required>
        <button class="btn">Add to Cart</button>
        </form>
        {% else %}
        <p style="color:red;"><b>Currently Out of Stock!</b></p>
        {% endif %}
        """
    return render_page("Product Details",content,p=product)

#User Registration
@app.route("/register",methods=["GET", "POST"])
def register():
    if request.method=="POST":
        name=request.form["name"].strip()
        email=request.form["email"].strip().lower()
        password=request.form["password"]

        if not name or not email or not password:
            flash("Please fill all the fields.","error")
            return redirect(url_for("register"))

        if len(password)<6:
            flash("Password must have at least 6 characters.","error")
            return redirect(url_for("register"))
        db=get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)))
            db.commit()
            flash("Registration successful. Please login.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
        finally:
            db.close()

    content="""
    <div class="form-box">
        <h2>Create Account</h2>

        <form method="POST">
            <label>Full Name</label>
            <input type="text" name="name" required>
            <label>Email Address</label>
            <input type="email" name="email" required>
            <label>Password</label>
            <input type="password" name="password"
                   minlength="6" required>
            <button class="btn" style="width:100%">Register</button>
        </form>
        <p>Already have an account?
            <a href="{{ url_for('login') }}">Login</a>
        </p>
    </div>
    """
    return render_page("Register", content)

#User login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        db=get_db()
        user=db.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        db.close()

        if user and check_password_hash(user["password"],password):
            session.clear()
            session["user_id"]=user["id"]
            session["user_name"]=user["name"]
            flash("Welcome back, " + user["name"] + "!")
            return redirect(url_for("home"))
        flash("Invalid email or password.","error")

    content="""
    <div class="form-box">
        <h2>User Login</h2>

        <form method="POST">
            <label>Email Address</label>
            <input type="email" name="email" required>

            <label>Password</label>
            <input type="password" name="password" required>

            <button class="btn" style="width:100%">Login</button>
        </form>

        <p>New customer?
            <a href="{{ url_for('register') }}">Create Account</a>
        </p>
    </div>
    """
    return render_page("Login", content)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out successfully.")
    return redirect(url_for("home"))

#Shopping Cart
@app.route("/add-to-cart/<int:product_id>",methods=["POST"])
def add_to_cart(product_id):
    if "user_id" not in session:
        flash("Please login to add products to your cart.","error")
        return redirect(url_for("login"))
    quantity=request.form.get("quantity",1,type=int)
    if quantity is None or quantity<1:
        flash("Please enter a valid quantity.","error")
        return redirect(url_for("product_detail",product_id=product_id))
    db=get_db()
    product=db.execute("SELECT * FROM products WHERE id=?",(product_id,)).fetchone()
    db.close()
    if not product:
        flash("Product not found.","error")
        return redirect(url_for("home"))

    if product["stock"]==0:
        flash("This product is out of stock.","error")
        return redirect(url_for("product_detail",product_id=product_id))
    cart=session.get("cart",{})
    key=str(product_id)
    current_quantity=cart.get(key,0)

    if current_quantity + quantity > product["stock"]:
        flash(f"Only {product['stock']} units are available in stock.","error")
        return redirect(url_for("product_detail",product_id=product_id))
    cart[key]=current_quantity+quantity
    session["cart"]=cart
    flash("Product added to cart successfully.")
    return redirect(url_for("cart"))

@app.route("/cart")
@login_required
def cart():
    cart_data=session.get("cart",{})
    items=[]
    total=0

    db=get_db()
    for product_id,quantity in cart_data.items():
        product=db.execute("SELECT * FROM products WHERE id=?",(int(product_id),)).fetchone()

        if product:
            subtotal=product["price"]*quantity
            total+=subtotal

            items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal
            })
    db.close()

    content="""
    <h2>My Shopping Cart</h2>

    {% if items %}
    <table>
        <tr>
            <th>Product</th>
            <th>Price</th>
            <th>Quantity</th>
            <th>Subtotal</th>
            <th>Action</th>
        </tr>

        {% for item in items %}
        <tr>
            <td>{{ item.product.name }}</td>
            <td>₹{{ "%.2f"|format(item.product.price) }}</td>
            <td>{{ item.quantity }}</td>
            <td>₹{{ "%.2f"|format(item.subtotal) }}</td>
            <td>
                <a class="btn red"
                   href="{{ url_for('remove_from_cart',
                       product_id=item.product.id) }}">
                    Remove
                </a>
            </td>
        </tr>
        {% endfor %}
    </table>

    <div class="total">Total: ₹{{ "%.2f"|format(total) }}</div>

    <a href="{{ url_for('home') }}" class="btn">Continue Shopping</a>
    <a href="{{ url_for('checkout') }}" class="btn green">Proceed to Checkout</a>

    {% else %}
        <h3>Your cart is empty.</h3>
        <a href="{{ url_for('home') }}" class="btn">Shop Now</a>
    {% endif %}
    """
    return render_page("Shopping Cart", content, items=items, total=total)

@app.route("/remove-from-cart/<int:product_id>")
@login_required
def remove_from_cart(product_id):
    cart=session.get("cart",{})
    cart.pop(str(product_id),None)
    session["cart"]=cart
    flash("Product removed from cart.")
    return redirect(url_for("cart"))


#Checkout and Order
@app.route("/checkout",methods=["GET","POST"])
@login_required
def checkout():
    cart_data=session.get("cart",{})
    if not cart_data:
        flash("Your cart is empty.","error")
        return redirect(url_for("home"))
    db=get_db()
    items=[]
    total=0
    for product_id,quantity in cart_data.items():
        product=db.execute("SELECT * FROM products WHERE id=?",(int(product_id),)).fetchone()
        if product:
            subtotal=product["price"]*quantity
            total+=subtotal
            items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal})
    if not items:
        session["cart"]={}
        db.close()
        flash("Your cart has no available products.","error")
        return redirect(url_for("home"))
    if request.method=="POST":
        address=request.form.get("address","").strip()
        payment_method=request.form.get("payment_method", "")
        if not address:
            db.close()
            flash("Please enter your delivery address.","error")
            return redirect(url_for("checkout"))
        allowed_methods=["UPI","Debit/Credit Card","Net Banking","Cash on Delivery"]
        if payment_method not in allowed_methods:
            db.close()
            flash("Please select a valid payment method.","error")
            return redirect(url_for("checkout"))

        # Simulate payment
        if payment_method=="Cash on Delivery":
            payment_status="Pending - COD"
            transaction_id="N/A"
        else:
            payment_status="Successful (Demo)"
            transaction_id="CARTIFY-" + secrets.token_hex(4).upper()
        try:
            db.execute("BEGIN IMMEDIATE")

            # Check product stock before placing the order
            for item in items:
                product_id=item["product"]["id"]
                quantity=item["quantity"]
                product = db.execute("SELECT stock FROM products WHERE id=?",(product_id,)).fetchone()
                if not product or product["stock"]<quantity:
                    raise ValueError(f"Insufficient stock for {item['product']['name']}")

            # Create order with payment details
            cursor=db.execute("""INSERT INTO orders(user_id,total,address,payment_method,payment_status, transaction_id)
            VALUES (?, ?, ?, ?, ?, ?)""",(session["user_id"],total,address,payment_method,payment_status,transaction_id))
            order_id=cursor.lastrowid

            # Save order items and reduce stock
            for item in items:
                p=item["product"]
                quantity=item["quantity"]
                db.execute("""INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)""",(order_id,p["id"],p["name"],quantity,p["price"]))
                result=db.execute("""UPDATE products SET stock=stock - ? WHERE id = ? AND stock >= ?""",(quantity, p["id"],quantity))
                if result.rowcount!=1:
                    raise ValueError("Stock is no longer available.")
            db.commit()
            session["cart"]={}
            if payment_method=="Cash on Delivery":
                flash("Order placed successfully with Cash on Delivery!")
            else:
                flash("Demo payment successful! Your order has been placed.")
            return redirect(url_for("my_orders"))
        except ValueError as e:
            db.rollback()
            flash(str(e),"error")
            return redirect(url_for("cart"))
        except Exception:
            db.rollback()
            flash("Order could not be placed. Please try again.", "error")
            return redirect(url_for("cart"))
        finally:
            db.close()
    db.close()
    content="""
    <div class="form-box">
        <h2>Checkout</h2>

        <h3>Order Summary</h3>

        {% for item in items %}
            <p>{{ item.product.name }} × {{ item.quantity }}
            — ₹{{ "%.2f"|format(item.subtotal) }}</p>
        {% endfor %}

        <h3 class="price">Total: ₹{{ "%.2f"|format(total) }}</h3>

        <form method="POST">
            <label>Delivery Address</label>
            <textarea name="address" rows="4"
                      placeholder="Enter your complete address"
                      required></textarea>

            <label>Select Payment Method</label>
            <select name="payment_method" required>
            <option value="">-- Select Payment Method --</option>
            <option value="UPI">UPI</option>
            <option value="Debit/Credit Card">Debit / Credit Card</option>
            <option value="Net Banking">Net Banking</option>
            <option value="Cash on Delivery">Cash on Delivery</option>
            </select>
            <p style="background:#eff6ff; padding:12px; border-radius:6px;">
            <b>Demo Payment Gateway</b><br>
            This is a payment for project demonstration.No real money will be deducted.
            </p>
            <button class="btn green" style="width:100%">
                Continue to Payment
            </button>
        </form>
    </div>
    """
    return render_page("Checkout",content,items=items,total=total)

@app.route("/my-orders")
@login_required
def my_orders():
    db=get_db()
    orders=db.execute("""SELECT * FROM orders WHERE user_id=? ORDER BY id DESC""",(session["user_id"],)).fetchall()
    db.close()

    content="""
    <h2>My Orders</h2>

    {% if orders %}
    <table>
        <tr>
            <th>Order ID</th>
            <th>Total Amount</th>
            <th>Payment Method</th>
            <th>Payment Status</th>
            <th>Transaction ID</th>
            <th>Order Status</th>
            <th>Date</th>
        </tr>

        {% for o in orders %}
        <tr>
            <td>#{{ o.id }}</td>
            <td>₹{{ "%.2f"|format(o.total) }}</td>
            <td>{{ o.payment_method }}</td>
            <td>{{ o.payment_status }}</td>
            <td>{{ o.transaction_id }}</td>
            <td>{{ o.status }}</td>
            <td>{{ o.created_at }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
        <p>You have not placed any orders yet.</p>
    {% endif %}
    """
    return render_page("My Orders",content,orders=orders)

#Admin Login
@app.route("/admin/login",methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["password"]
        if username==ADMIN_USERNAME and password==ADMIN_PASSWORD:
            session.clear()
            session["admin"]=True
            flash("Admin login successful.")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")

    content="""
    <div class="form-box">
        <h2>Admin Login</h2>

        <form method="POST">
            <label>Username</label>
            <input type="text" name="username" required>

            <label>Password</label>
            <input type="password" name="password" required>

            <button class="btn" style="width:100%">Admin Login</button>
        </form>
    </div>
    """
    return render_page("Admin Login",content)

#Admin Dashboard
@app.route("/admin")
@admin_required
def admin_dashboard():
    db=get_db()
    products=db.execute("SELECT * FROM products ORDER BY id ASC").fetchall()
    total_products=db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_orders=db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_users=db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    db.close()
    content="""
    <h2>Admin Dashboard</h2>
    <div class="grid">
        <div class="card">
            <h3>Total Products</h3>
            <h1>{{ total_products }}</h1>
        </div>
        <div class="card">
            <h3>Total Orders</h3>
            <h1>{{ total_orders }}</h1>
        </div>
        <div class="card">
            <h3>Registered Users</h3>
            <h1>{{ total_users }}</h1>
        </div>
    </div>
    <br>
    <h2>Manage Products</h2>
    <a href="{{ url_for('add_product') }}" class="btn green">
        + Add New Product
    </a>
    <br><br>
    <table>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Category</th>
            <th>Price</th>
            <th>Available Stock</th>
            <th>Action</th>
        </tr>
        {% for p in products %}
        <tr>
            <td>{{ p.id }}</td>
            <td>{{ p.name }}</td>
            <td>{{ p.category }}</td>
            <td>₹{{ p.price }}</td>
            <td>
                {% if p.stock == 0 %}
                    <span style="color:red;">Out of Stock</span>
                {% elif p.stock <= 5 %}
                    <span style="color:orange;">{{ p.stock }} (Low Stock)</span>
                {% else %}
                    <span style="color:green;">{{ p.stock }}</span>
                {% endif %}
            </td>
            <td>
                <a class="btn green"
                   href="{{ url_for('update_stock', product_id=p.id) }}">
                   Update Stock
                </a>
                <a class="btn red"
                   href="{{ url_for('delete_product', product_id=p.id) }}"
                   onclick="return confirm('Delete this product?')">
                   Delete
                </a>
            </td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <a href="{{ url_for('admin_orders') }}" class="btn">
        View All Orders
    </a>
    """
    return render_page("Admin Dashboard",content,products=products,total_products=total_products,
        total_orders=total_orders,
        total_users=total_users)

#Add Product
@app.route("/admin/add-product",methods=["GET","POST"])
@admin_required
def add_product():
    if request.method=="POST":
        name=request.form["name"].strip()
        category=request.form["category"].strip()
        description=request.form["description"].strip()
        image=request.form["image"].strip() or "📦"
        try:
            price=float(request.form["price"])
            if price<=0 or price>10000000:
                raise ValueError
        except ValueError:
            flash("Enter a valid product price.","error")
            return redirect(url_for("add_product"))

        #check stock quantity
        try:
            stock=int(request.form["stock"])
            if stock<0:
                raise ValueError
        except ValueError:
            flash("Enter a valid stock quantity.","error")
            return redirect(url_for("add_product"))
        
        if not name or not category:
            flash("Product name and category are required.","error")
            return redirect(url_for("add_product"))
        db=get_db()
        db.execute("""INSERT INTO products (name,category,price,description,image,stock)
        VALUES (?, ?, ?, ?, ?, ?)""",(name,category,price,description,image,stock))
        db.commit()
        db.close()
        flash("Product added successfully!")
        return redirect(url_for("admin_dashboard"))

    content="""
    <div class="form-box">
        <h2>Add New Product</h2>

        <form method="POST">
            <label>Product Name</label>
            <input type="text" name="name" required>

            <label>Category</label>
            <input type="text" name="category" required>

            <label>Price (₹)</label>
            <input type="number" name="price" min="0.01" step="0.01" required>
            
            <label>Available Stock</label>
            <input type="number" name="stock" min="0" required>

            <label>Description</label>
            <textarea name="description" rows="3"></textarea>

            <label>Product Emoji</label>
            <input type="text" name="image" placeholder="Example: 🎧">

            <button class="btn green" style="width:100%">
                Add Product
            </button>
        </form>
    </div>
    """
    return render_page("Add Product", content)

# Update Stock
@app.route("/admin/update-stock/<int:product_id>", methods=["GET", "POST"])
@admin_required
def update_stock(product_id):
    db=get_db()
    product=db.execute("SELECT * FROM products WHERE id=?",(product_id,)).fetchone()
    if not product:
        db.close()
        flash("Product not found.")
        return redirect(url_for("admin_dashboard"))
    if request.method=="POST":
        try:
            new_stock=int(request.form.get("stock"))
            if new_stock < 0:
                raise ValueError
        except (ValueError,TypeError):
            db.close()
            flash("Please enter a valid stock quantity.")
            return redirect(url_for("update_stock",product_id=product_id))
        db.execute("UPDATE products SET stock=? WHERE id=?",(new_stock,product_id))
        db.commit()
        db.close()
        flash("Stock updated successfully!")
        return redirect(url_for("admin_dashboard"))
    content="""
    <div class="form-box">
        <h2 style="text-align:center;">
            Manage Product Stock
        </h2>
        <h3 style="text-align:center;">
            {{ p.name }}
        </h3>
        <p style="text-align:center; color:#555;">
            Current Available Stock
        </p>
        <form method="POST">
            <div style="
                display:flex;
                align-items:center;
                justify-content:center;
                gap:20px;
                margin:25px 0;
            ">
                <button type="button"
                        onclick="changeStock(-1)"
                        style="
                            width:55px;
                            height:55px;
                            font-size:30px;
                            border:none;
                            border-radius:10px;
                            background:#dc2626;
                            color:white;
                            cursor:pointer;
                        ">
                    −
                </button>
                <input type="number"
                       id="stock"
                       name="stock"
                       value="{{ p.stock }}"
                       min="0"
                       required
                       style="
                           width:120px;
                           height:55px;
                           text-align:center;
                           font-size:28px;
                           font-weight:bold;
                           border:2px solid #ddd;
                           border-radius:10px;
                       ">
                <button type="button"
                        onclick="changeStock(1)"
                        style="
                            width:55px;
                            height:55px;
                            font-size:30px;
                            border:none;
                            border-radius:10px;
                            background:#16a34a;
                            color:white;
                            cursor:pointer;
                        ">
                    +
                </button>
            </div>
            <p style="text-align:center; color:#666;">
                Use + to increase and − to decrease stock.
            </p>
            <button type="submit"
                    class="btn green"
                    style="width:100%; margin-top:15px;">
                Save Stock
            </button>
        </form>
        <br>
        <a href="{{ url_for('admin_dashboard') }}"
           class="btn"
           style="display:block; text-align:center;">
            Back to Dashboard
        </a>
    </div>
    <script>
    function changeStock(value) {
        let input = document.getElementById("stock");
        let current = parseInt(input.value) || 0;
        let updated = current + value;
        if (updated >= 0) {
            input.value = updated;
        }
    }
    </script>
    """
    return render_page("Manage Stock",content,p=product)

#Delete Product
@app.route("/admin/delete-product/<int:product_id>")
@admin_required
def delete_product(product_id):
    db=get_db()
    db.execute("DELETE FROM products WHERE id=?",(product_id,))
    db.commit()
    db.close()
    flash("Product deleted successfully.")
    return redirect(url_for("admin_dashboard"))

#Admin Orders
@app.route("/admin/orders")
@admin_required
def admin_orders():
    db=get_db()
    orders=db.execute("""SELECT orders.*, users.name, users.email FROM orders
        JOIN users ON orders.user_id=users.id ORDER BY orders.id DESC""").fetchall()
    db.close()

    content="""
    <h2>Customer Orders</h2>
    {% if orders %}
    <table>
        <tr>
            <th>Order ID</th>
            <th>Customer</th>
            <th>Email</th>
            <th>Total</th>
            <th>Payment Method</th>
            <th>Payment Status</th>
            <th>Transaction ID</th>
            <th>Address</th>
            <th>Status</th>
        </tr>
        {% for o in orders %}
        <tr>
            <td>#{{ o.id }}</td>
            <td>{{ o.name }}</td>
            <td>{{ o.email }}</td>
            <td>₹{{ "%.2f"|format(o.total) }}</td>
            <td>{{ o.payment_method }}</td>
            <td>{{ o.payment_status }}</td>
            <td>{{ o.transaction_id }}</td>
            <td>{{ o.address }}</td>
            <td>{{ o.status }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
        <p>No orders have been placed yet.</p>
    {% endif %}
    <a href="{{ url_for('admin_dashboard') }}" class="btn">
        Back to Dashboard
    </a>
    """
    return render_page("Customer Orders", content, orders=orders)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Admin logged out successfully.")
    return redirect(url_for("home"))

#Run
if __name__=="__main__":
    init_db()
    app.run(debug=True)