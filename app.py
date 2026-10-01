import hashlib
import base64
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------
# DATABASE INITIALIZATION & CONNECTIVITY (DATABASE LOCK FIXED)
# ---------------------------------------------------------
DB_NAME = str(Path(__file__).resolve().with_name("ebook_store.db"))

def get_connection():
    # กำหนด timeout 20 วินาที และเปิดโหมด WAL เพื่อรองรับการอ่าน-เขียนพร้อมกัน
    conn = sqlite3.connect(DB_NAME, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def seed_data(cursor):
    # Insert Roles
    cursor.executemany("INSERT INTO roles (role_id, role_name) VALUES (?, ?)", [
        (1, 'Admin'), (2, 'Customer')
    ])
    
    # Insert Users
    users = [
        ('Admin User', 'admin@ebook.com', hash_pass('admin123'), 1),
        ('สมชาย สายเปย์', 'somchai@gmail.com', hash_pass('user123'), 2),
        ('มณี เรียนดี', 'manee@gmail.com', hash_pass('user123'), 2),
        ('กิตติพงษ์ นักอ่าน', 'kitti@gmail.com', hash_pass('user123'), 2)
    ]
    cursor.executemany("INSERT INTO users (full_name, email, password_hash, role_id) VALUES (?, ?, ?, ?)", users)

    # Insert Categories
    categories = [('เทคโนโลยี',), ('การพัฒนาตนเอง',), ('การเงินและการลงทุน',), ('นิยาย',)]
    cursor.executemany("INSERT INTO categories (category_name) VALUES (?)", categories)

    # Insert Authors
    authors = [('ดร.อนันต์ ไอที',), ('โค้ชหนุ่ม การเงิน',), ('อรุณรุ่ง วรรณกรรม',), ('ครูเพ็ญ พัฒนาตน',)]
    cursor.executemany("INSERT INTO authors (author_name) VALUES (?)", authors)

    # Insert Ebooks
    ebooks = [
        ('Python & Data Science 101', 1, 1, 350.00, 'ปูพื้นฐานการเขียนโค้ดวิเคราะห์ข้อมูล', 'https://picsum.photos/seed/py/200/280'),
        ('ปลดล็อคอิสรภาพทางการเงิน', 2, 3, 290.00, 'คู่มือวางแผนการเงินฉบับทำได้จริง', 'https://picsum.photos/seed/money/200/280'),
        ('คิดช้า ให้ได้เรื่อง (Slow Thinking)', 4, 2, 250.00, 'การตัดสินใจอย่างมีประสิทธิภาพ', 'https://picsum.photos/seed/think/200/280'),
        ('ปาฏิหาริย์ร้านหนังสือคิโนะ', 3, 4, 199.00, 'นวนิยายสร้างแรงบันดาลใจอบอุ่นหัวใจ', 'https://picsum.photos/seed/novel/200/280'),
        ('SQL & Database Design Pro', 1, 1, 420.00, 'ออกแบบฐานข้อมูล 3NF และปรับแต่ง Query', 'https://picsum.photos/seed/sql/200/280')
    ]
    cursor.executemany("INSERT INTO ebooks (title, author_id, category_id, price, description, cover_image_url) VALUES (?, ?, ?, ?, ?, ?)", ebooks)

    # Download Links
    links = [
        (1, 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'),
        (2, 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'),
        (3, 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'),
        (4, 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'),
        (5, 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf')
    ]
    cursor.executemany("INSERT INTO download_links (ebook_id, download_url) VALUES (?, ?)", links)

    # Generate 32 Mock Orders
    statuses = ['CONFIRMED', 'PAID', 'PENDING', 'CANCELLED']
    dates = [
        '2026-09-01 10:00:00', '2026-09-03 14:20:00', '2026-09-05 09:15:00', 
        '2026-09-10 18:30:00', '2026-09-15 11:45:00', '2026-09-20 16:10:00',
        '2026-09-25 20:00:00', '2026-09-28 13:00:00'
    ]
    
    order_id_cnt = 1
    for i in range(32):
        u_id = (i % 3) + 2 # Customer 2, 3, 4
        st_val = statuses[i % 4]
        dt_val = dates[i % len(dates)]
        e_id = (i % 5) + 1
        price = [350.00, 290.00, 250.00, 199.00, 420.00][e_id - 1]
        
        cursor.execute("INSERT INTO orders (user_id, total_amount, status, created_at) VALUES (?, ?, ?, ?)",
                       (u_id, price, st_val, dt_val))
        cursor.execute("INSERT INTO order_items (order_id, ebook_id, unit_price, quantity) VALUES (?, ?, ?, ?)",
                       (order_id_cnt, e_id, price, 1))
        
        if st_val in ['PAID', 'CONFIRMED']:
            cursor.execute("INSERT INTO payments (order_id, payment_method, payment_slip_url, paid_at) VALUES (?, ?, ?, ?)",
                           (order_id_cnt, 'PromptPay QR', 'https://via.placeholder.com/150/0000FF/808080?text=MockSlip', dt_val))
        order_id_cnt += 1

@st.cache_resource # ป้องกันการสร้างตารางซ้ำซ้อนขณะ Streamlit ทำการ Rerun
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Roles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE
        );
    ''')
    
    # 2. Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role_id INTEGER NOT NULL DEFAULT 2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(role_id)
        );
    ''')
    
    # 3. Categories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        );
    ''')

    # 4. Authors
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            author_id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_name TEXT NOT NULL
        );
    ''')
    
    # 5. Ebooks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ebooks (
            ebook_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            description TEXT,
            cover_image_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES authors(author_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        );
    ''')

    # 6. Download Links
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS download_links (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ebook_id INTEGER NOT NULL UNIQUE,
            download_url TEXT NOT NULL,
            FOREIGN KEY (ebook_id) REFERENCES ebooks(ebook_id) ON DELETE CASCADE
        );
    ''')

    # 7. Orders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL CHECK(total_amount >= 0),
            status TEXT CHECK(status IN ('PENDING', 'PAID', 'CONFIRMED', 'CANCELLED')) DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    ''')

    # 8. Order Items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            ebook_id INTEGER NOT NULL,
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            quantity INTEGER NOT NULL CHECK(quantity > 0) DEFAULT 1,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (ebook_id) REFERENCES ebooks(ebook_id)
        );
    ''')

    # 9. Payments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL UNIQUE,
            payment_method TEXT NOT NULL,
            payment_slip_url TEXT,
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
    ''')
    
    conn.commit()
    
    # Seed Data Initializer if empty
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:
        seed_data(cursor)
        conn.commit()
        
    conn.close()

# ---------------------------------------------------------
# APPLICATION SETUP & SESSION STATE
# ---------------------------------------------------------
st.set_page_config(page_title="E-Book Store & Admin Management", layout="wide", page_icon="📚")
init_db()

if 'user' not in st.session_state:
    st.session_state.user = None
if 'cart' not in st.session_state:
    st.session_state.cart = {} # {ebook_id: qty}

# ---------------------------------------------------------
# AUTHENTICATION MODULE
# ---------------------------------------------------------
def login():
    st.sidebar.subheader("🔐 เข้าสู่ระบบ")
    email = st.sidebar.text_input("อีเมล", key="login_email")
    password = st.sidebar.text_input("รหัสผ่าน", type="password", key="login_pass")
    
    if st.sidebar.button("เข้าสู่ระบบ", type="primary"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.full_name, u.email, u.role_id, r.role_name 
            FROM users u JOIN roles r ON u.role_id = r.role_id 
            WHERE u.email = ? AND u.password_hash = ?
        """, (email, hash_pass(password)))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            st.session_state.user = {
                'id': user[0], 'name': user[1], 'email': user[2],
                'role_id': user[3], 'role_name': user[4]
            }
            st.sidebar.success(f"ยินดีต้อนรับคุณ {user[1]}")
            st.rerun()
        else:
            st.sidebar.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")

def register():
    st.sidebar.subheader("📝 สมัครสมาชิก")
    name = st.sidebar.text_input("ชื่อ-นามสกุล", key="reg_name")
    email = st.sidebar.text_input("อีเมล", key="reg_email")
    password = st.sidebar.text_input("รหัสผ่าน", type="password", key="reg_pass")
    
    if st.sidebar.button("สมัครสมาชิก"):
        if not name or not email or not password:
            st.sidebar.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")
            return
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                           (name, email, hash_pass(password)))
            conn.commit()
            st.sidebar.success("สมัครสมาชิกสำเร็จ! กรุณาล็อกอิน")
        except sqlite3.IntegrityError:
            st.sidebar.error("อีเมลนี้ถูกใช้งานในระบบแล้ว")
        finally:
            conn.close()

# ---------------------------------------------------------
# CUSTOMER FRONT-END
# ---------------------------------------------------------
def render_storefront():
    st.title("📚 ร้านค้า E-Book ออนไลน์")
    
    conn = get_connection()
    categories_df = pd.read_sql_query("SELECT * FROM categories", conn)
    
    col1, col2 = st.columns([2, 1])
    search_term = col1.text_input("🔍 ค้นหา E-Book ด้วยชื่อหรือคำสำคัญ")
    cat_filter = col2.selectbox("🏷️ หมวดหมู่", ["ทั้งหมด"] + categories_df['category_name'].tolist())
    
    query = """
        SELECT e.ebook_id, e.title, a.author_name, c.category_name, e.price, e.description, e.cover_image_url, e.is_active
        FROM ebooks e
        JOIN authors a ON e.author_id = a.author_id
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.is_active = 1
    """
    params = []
    
    if search_term:
        query += " AND (e.title LIKE ? OR e.description LIKE ? OR a.author_name LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
    if cat_filter != "ทั้งหมด":
        query += " AND c.category_name = ?"
        params.append(cat_filter)
        
    ebooks_df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    st.divider()
    
    cols = st.columns(3)
    for idx, row in ebooks_df.iterrows():
        with cols[idx % 3]:
            st.image(row['cover_image_url'], width=150)
            st.subheader(row['title'])
            st.caption(f"ผู้แต่ง: {row['author_name']} | หมวดหมู่: {row['category_name']}")
            st.markdown(f"**ราคา: {row['price']:.2f} บาท**")
            st.write(row['description'])
            st.success("🟢 สถานะ: พร้อมขาย" if row['is_active'] == 1 else "🔴 สถานะ: ปิดการขาย")
            
            if st.button(f"🛒 ใส่ตะกร้า", key=f"add_{row['ebook_id']}"):
                eid = row['ebook_id']
                st.session_state.cart[eid] = st.session_state.cart.get(eid, 0) + 1
                st.success("เพิ่มสินค้าลงตะกร้าแล้ว!")

def render_cart():
    st.title("🛒 ตะกร้าสินค้า")
    if not st.session_state.cart:
        st.info("ยังไม่มีสินค้าในตะกร้า")
        return
        
    conn = get_connection()
    placeholders = ','.join(['?'] * len(st.session_state.cart))
    query = f"SELECT ebook_id, title, price FROM ebooks WHERE ebook_id IN ({placeholders})"
    cart_items = pd.read_sql_query(query, conn, params=list(st.session_state.cart.keys()))
    conn.close()
    
    total_price = 0.0
    st.subheader("รายการสินค้าที่เลือก")
    
    for _, row in cart_items.iterrows():
        eid = row['ebook_id']
        qty = st.session_state.cart[eid]
        item_total = row['price'] * qty
        total_price += item_total
        
        # ปรับแบ่งเป็น 5 คอลัมน์ เพื่อใส่ปุ่ม ➕ เพิ่มเติม
        c1, c2, c3, c4, c5 = st.columns([3, 0.6, 1.2, 0.6, 1])
        c1.write(f"**{row['title']}** ({row['price']:.2f} ฿)")
        
        # ปุ่มลดจำนวน ➖
        if c2.button("➖", key=f"dec_{eid}"):
            if qty > 1:
                st.session_state.cart[eid] -= 1
            else:
                del st.session_state.cart[eid]
            st.rerun()
            
        c3.write(f"จำนวน: **{qty}**")
        
        # ปุ่มเพิ่มจำนวน ➕
        if c4.button("➕", key=f"inc_{eid}"):
            st.session_state.cart[eid] += 1
            st.rerun()
            
        # ปุ่มลบรายการ ❌
        if c5.button("❌ ลบ", key=f"del_{eid}"):
            del st.session_state.cart[eid]
            st.rerun()
            
    st.divider()
    st.markdown(f"### ยอดรวมทั้งหมด: **{total_price:.2f} บาท**")
    
    if st.button("✅ ยืนยันสั่งซื้อ (Checkout)", type="primary"):
        if not st.session_state.user:
            st.error("กรุณาล็อกอินก่อนทำการสั่งซื้อ")
            return
            
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, 'PENDING')",
                       (st.session_state.user['id'], total_price))
        order_id = cursor.lastrowid
        
        for _, row in cart_items.iterrows():
            eid = row['ebook_id']
            qty = st.session_state.cart[eid]
            cursor.execute("INSERT INTO order_items (order_id, ebook_id, unit_price, quantity) VALUES (?, ?, ?, ?)",
                           (order_id, eid, row['price'], qty))
                           
        conn.commit()
        conn.close()
        st.session_state.cart = {}
        st.success(f"สร้างคำสั่งซื้อ #{order_id} เรียบร้อยแล้ว! กรุณาชำระเงินที่หน้าประวัติคำสั่งซื้อ")

def render_my_orders():
    st.title("📦 ประวัติคำสั่งซื้อและการดาวน์โหลด")
    if not st.session_state.user:
        st.warning("กรุณาล็อกอินเพื่อดูประวัติคำสั่งซื้อ")
        return
        
    conn = get_connection()
    user_id = st.session_state.user['id']
    
    orders = pd.read_sql_query("""
        SELECT order_id, total_amount, status, created_at 
        FROM orders WHERE user_id = ? ORDER BY order_id DESC
    """, conn, params=[user_id])
    
    if orders.empty:
        st.info("ไม่พบประวัติการสั่งซื้อ")
        conn.close()
        return

    for _, ord_row in orders.iterrows():
        oid = ord_row['order_id']
        st.markdown(f"### คำสั่งซื้อ #{oid} | วันที่: {ord_row['created_at']}")
        st.write(f"สถานะ: **{ord_row['status']}** | ยอดรวม: **{ord_row['total_amount']:.2f} บาท**")
        
        # Order items
        items = pd.read_sql_query("""
            SELECT e.title, oi.unit_price, oi.quantity, dl.download_url
            FROM order_items oi
            JOIN ebooks e ON oi.ebook_id = e.ebook_id
            LEFT JOIN download_links dl ON e.ebook_id = dl.ebook_id
            WHERE oi.order_id = ?
        """, conn, params=[oid])
        
        st.table(items[['title', 'unit_price', 'quantity']])
        
        # Payment / Download Logic
        if ord_row['status'] == 'PENDING':
            st.info("💳 กรุณาชำระเงินจำลอง")
            pm = st.selectbox("เลือกวิธีชำระเงิน", ["PromptPay QR", "โอนผ่านธนาคารจำลอง"], key=f"pm_{oid}")
            slip = st.file_uploader("แนบสลิปจำลอง", type=['png', 'jpg', 'jpeg'], key=f"slip_{oid}")
            if st.button("ส่งหลักฐานชำระเงิน", key=f"pay_btn_{oid}"):
                slip_data = None
                if slip is not None:
                    mime = slip.type or "image/png"
                    encoded_slip = base64.b64encode(slip.getvalue()).decode("ascii")
                    slip_data = f"data:{mime};base64,{encoded_slip}"
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO payments (order_id, payment_method, payment_slip_url)
                                  VALUES (?, ?, ?)
                                  ON CONFLICT(order_id) DO UPDATE SET
                                  payment_method=excluded.payment_method,
                                  payment_slip_url=excluded.payment_slip_url,
                                  paid_at=CURRENT_TIMESTAMP""", (oid, pm, slip_data))
                cursor.execute("UPDATE orders SET status = 'PAID' WHERE order_id = ?", (oid,))
                conn.commit()
                st.success("บันทึกการชำระเงินจำลองแล้ว! รอผู้ดูแลอนุมัติคำสั่งซื้อ")
                st.rerun()
                
        elif ord_row['status'] == 'PAID':
            st.warning("⏳ รอผู้ดูแลร้านตรวจสอบหลักฐานชำระเงิน (ยังไม่สามารถดาวน์โหลดได้)")
            
        elif ord_row['status'] == 'CONFIRMED':
            st.success("🎉 ชำระเงินเรียบร้อยแล้ว! สามารถดาวน์โหลด E-Book ได้ด้านล่าง:")
            for _, item in items.iterrows():
                if pd.notna(item['download_url']) and str(item['download_url']).strip():
                    st.markdown(f"📥 **[{item['title']}]({item['download_url']})** (คลิกเพื่อดาวน์โหลด PDF)")
                else:
                    st.caption(f"{item['title']}: ยังไม่มีลิงก์ดาวน์โหลด")
                
        elif ord_row['status'] == 'CANCELLED':
            st.error("❌ คำสั่งซื้อนี้ถูกยกเลิก")
            
        st.divider()
        
    conn.close()

# ---------------------------------------------------------
# CUSTOMER PROFILE EDITING (เพิ่มฟังก์ชันที่ยังขาด)
# ---------------------------------------------------------
def render_profile():
    st.title("👤 แก้ไขข้อมูลพื้นฐาน")
    if not st.session_state.user:
        st.warning("กรุณาเข้าสู่ระบบก่อนแก้ไขข้อมูล")
        return
    conn = get_connection()
    try:
        row = conn.execute("SELECT full_name, email FROM users WHERE user_id = ?",
                           (st.session_state.user['id'],)).fetchone()
        if not row:
            st.error("ไม่พบข้อมูลผู้ใช้")
            return
        with st.form("profile_form"):
            name = st.text_input("ชื่อ-นามสกุล", value=row[0])
            email = st.text_input("อีเมล", value=row[1])
            new_password = st.text_input("รหัสผ่านใหม่ (เว้นว่างหากไม่เปลี่ยน)", type="password")
            submitted = st.form_submit_button("บันทึกข้อมูล")
        if submitted:
            if not name.strip() or "@" not in email:
                st.error("กรุณากรอกชื่อและอีเมลที่ถูกต้อง")
            else:
                cursor = conn.cursor()
                try:
                    if new_password:
                        cursor.execute("UPDATE users SET full_name=?, email=?, password_hash=? WHERE user_id=?",
                                       (name.strip(), email.strip(), hash_pass(new_password), st.session_state.user['id']))
                    else:
                        cursor.execute("UPDATE users SET full_name=?, email=? WHERE user_id=?",
                                       (name.strip(), email.strip(), st.session_state.user['id']))
                    conn.commit()
                    st.session_state.user['name'] = name.strip()
                    st.session_state.user['email'] = email.strip()
                    st.success("บันทึกข้อมูลส่วนตัวแล้ว")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("อีเมลนี้ถูกใช้งานแล้ว")
    finally:
        conn.close()


def ebooks_export_csv(conn):
    df = pd.read_sql_query("""
        SELECT e.ebook_id, e.title, a.author_name, c.category_name, e.price,
               e.description, e.is_active, dl.download_url
        FROM ebooks e
        LEFT JOIN authors a ON e.author_id = a.author_id
        LEFT JOIN categories c ON e.category_id = c.category_id
        LEFT JOIN download_links dl ON e.ebook_id = dl.ebook_id
        ORDER BY e.ebook_id
    """, conn)
    return df.to_csv(index=False).encode("utf-8-sig")


# ---------------------------------------------------------
# ADMIN BACKOFFICE MODULE
# ---------------------------------------------------------
def render_admin_dashboard():
    st.title("⚙️ ระบบบริหารจัดการหลังบ้าน (Admin)")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard รายงาน", "📚 จัดการ E-Book", "📦 จัดการคำสั่งซื้อ", "🏷️ จัดการหมวดหมู่", "👥 จัดการผู้ใช้"])
    conn = get_connection()
    
    with tab1:
        st.subheader("📊 รายงานวิเคราะห์ข้อมูลเชิงธุรกิจ")
        
        # 1. Total Sales Trend
        sales_df = pd.read_sql_query("""
            SELECT DATE(created_at) as sale_date, SUM(total_amount) as daily_sales
            FROM orders WHERE status = 'CONFIRMED'
            GROUP BY DATE(created_at) ORDER BY sale_date
        """, conn)
        fig1 = px.line(sales_df, x='sale_date', y='daily_sales', title="1. แนวโน้มยอดขายตามช่วงเวลา")
        st.plotly_chart(fig1, use_container_width=True)
        
        # 2. Top Selling Ebooks
        top_df = pd.read_sql_query("""
            SELECT e.title, SUM(oi.quantity) as total_sold
            FROM order_items oi
            JOIN ebooks e ON oi.ebook_id = e.ebook_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status = 'CONFIRMED'
            GROUP BY e.ebook_id ORDER BY total_sold DESC LIMIT 5
        """, conn)
        fig2 = px.bar(top_df, x='title', y='total_sold', title="2. Top 5 E-Book ขายดีที่สุด")
        st.plotly_chart(fig2, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            # 3. Category Sales
            cat_df = pd.read_sql_query("""
                SELECT c.category_name, SUM(oi.quantity * oi.unit_price) as category_sales
                FROM order_items oi
                JOIN ebooks e ON oi.ebook_id = e.ebook_id
                JOIN categories c ON e.category_id = c.category_id
                JOIN orders o ON oi.order_id = o.order_id
                WHERE o.status = 'CONFIRMED'
                GROUP BY c.category_id
            """, conn)
            fig3 = px.pie(cat_df, values='category_sales', names='category_name', title="3. ยอดขายแยกตามหมวดหมู่")
            st.plotly_chart(fig3, use_container_width=True)

        with col_b:
            # 4. Customer Behavior
            cust_df = pd.read_sql_query("""
                SELECT u.full_name, SUM(o.total_amount) as total_spent
                FROM orders o JOIN users u ON o.user_id = u.user_id
                WHERE o.status = 'CONFIRMED'
                GROUP BY u.user_id ORDER BY total_spent DESC
            """, conn)
            fig4 = px.bar(cust_df, x='full_name', y='total_spent', title="4. พฤติกรรมยอดซื้อสะสมของลูกค้า VIP")
            st.plotly_chart(fig4, use_container_width=True)

        st.subheader("📤 ส่งออกรายงาน")
        export_df = pd.read_sql_query("""
            SELECT o.order_id, u.full_name, u.email, o.total_amount, o.status, o.created_at
            FROM orders o JOIN users u ON o.user_id = u.user_id
            ORDER BY o.order_id DESC
        """, conn)
        st.download_button("ดาวน์โหลดรายงานคำสั่งซื้อ (CSV)",
                           data=export_df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="ebook_orders_report.csv", mime="text/csv")
        st.download_button("ดาวน์โหลดรายการ E-Book (CSV)",
                           data=ebooks_export_csv(conn), file_name="ebook_inventory_report.csv",
                           mime="text/csv")

    with tab2:
        st.subheader("📚 จัดการรายการ E-Book (CRUD)")
        
        # ดึงข้อมูล E-Book ทั้งหมดรวมทั้งที่ถูกซ่อนไว้
        ebooks_all = pd.read_sql_query("""
            SELECT e.ebook_id, e.title, a.author_name, c.category_name, e.price, e.is_active, dl.download_url
            FROM ebooks e
            JOIN authors a ON e.author_id = a.author_id
            JOIN categories c ON e.category_id = c.category_id
            LEFT JOIN download_links dl ON e.ebook_id = dl.ebook_id
        """, conn)
        st.dataframe(ebooks_all, use_container_width=True)
        
        st.divider()
        action = st.radio("เลือกการทำงาน:", ["➕ เพิ่ม E-Book เล่มใหม่", "✏️ แก้ไข E-Book", "❌ เปิด/ปิด การจำหน่าย"], horizontal=True)
        
        # 1. เพิ่ม E-Book
        if action == "➕ เพิ่ม E-Book เล่มใหม่":
            with st.form("add_ebook_form"):
                new_title = st.text_input("ชื่อหนังสือ")
                authors_df = pd.read_sql_query("SELECT author_id, author_name FROM authors ORDER BY author_name", conn)
                categories_for_ebook = pd.read_sql_query("SELECT category_id, category_name FROM categories ORDER BY category_name", conn)
                if authors_df.empty or categories_for_ebook.empty:
                    st.warning("ต้องมีข้อมูลผู้แต่งและหมวดหมู่ก่อนเพิ่ม E-Book")
                    new_author_id = new_category_id = None
                else:
                    author_labels = dict(zip(authors_df['author_name'], authors_df['author_id']))
                    category_labels = dict(zip(categories_for_ebook['category_name'], categories_for_ebook['category_id']))
                    selected_author = st.selectbox("ผู้แต่ง", list(author_labels.keys()), key="add_author")
                    selected_category = st.selectbox("หมวดหมู่", list(category_labels.keys()), key="add_category")
                    new_author_id = author_labels[selected_author]
                    new_category_id = category_labels[selected_category]
                new_price = st.number_input("ราคา", min_value=0.0, value=200.0)
                new_desc = st.text_area("คำอธิบาย")
                new_url = st.text_input("URL ภาพปก", value="https://picsum.photos/seed/new/200/280")
                new_dl = st.text_input("URL ดาวน์โหลด PDF", value="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf")
                submit_eb = st.form_submit_button("บันทึกหนังสือใหม่")
                
                if submit_eb and new_title and new_author_id is not None and new_category_id is not None:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO ebooks (title, author_id, category_id, price, description, cover_image_url) VALUES (?, ?, ?, ?, ?, ?)",
                                   (new_title, new_author_id, new_category_id, new_price, new_desc, new_url))
                    new_id = cursor.lastrowid
                    cursor.execute("INSERT INTO download_links (ebook_id, download_url) VALUES (?, ?)", (new_id, new_dl))
                    conn.commit()
                    st.success("เพิ่ม E-Book สำเร็จ!")
                    st.rerun()

        # 2. แก้ไข E-Book
        elif action == "✏️ แก้ไข E-Book":
            ebook_list = ebooks_all['ebook_id'].tolist()
            if ebook_list:
                selected_id = st.selectbox("เลือก ID หนังสือที่ต้องการแก้ไข", ebook_list)
                target = pd.read_sql_query("SELECT * FROM ebooks WHERE ebook_id = ?", conn, params=[selected_id]).iloc[0]
                
                with st.form("edit_ebook_form"):
                    edit_title = st.text_input("ชื่อหนังสือ", value=target['title'])
                    edit_price = st.number_input("ราคา", min_value=0.0, value=float(target['price']))
                    edit_desc = st.text_area("คำอธิบาย", value=target['description'] or '')
                    edit_cover = st.text_input("URL ภาพปก", value=target['cover_image_url'] or '')
                    current_dl = conn.execute("SELECT download_url FROM download_links WHERE ebook_id=?", (selected_id,)).fetchone()
                    edit_dl = st.text_input("URL ดาวน์โหลด PDF/EPUB", value=current_dl[0] if current_dl else '')
                    author_rows = pd.read_sql_query("SELECT author_id, author_name FROM authors ORDER BY author_name", conn)
                    category_rows = pd.read_sql_query("SELECT category_id, category_name FROM categories ORDER BY category_name", conn)
                    author_names = dict(zip(author_rows['author_name'], author_rows['author_id']))
                    category_names = dict(zip(category_rows['category_name'], category_rows['category_id']))
                    current_author = conn.execute("SELECT author_name FROM authors WHERE author_id=?", (target['author_id'],)).fetchone()
                    current_category = conn.execute("SELECT category_name FROM categories WHERE category_id=?", (target['category_id'],)).fetchone()
                    edit_author_name = st.selectbox("ผู้แต่ง", list(author_names), index=list(author_names).index(current_author[0]) if current_author and current_author[0] in author_names else 0)
                    edit_category_name = st.selectbox("หมวดหมู่", list(category_names), index=list(category_names).index(current_category[0]) if current_category and current_category[0] in category_names else 0)
                    submit_edit = st.form_submit_button("บันทึกการแก้ไข")
                    
                    if submit_edit:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE ebooks 
                            SET title = ?, author_id = ?, category_id = ?, price = ?, description = ?, cover_image_url = ?
                            WHERE ebook_id = ?
                        """, (edit_title, author_names[edit_author_name], category_names[edit_category_name], edit_price, edit_desc, edit_cover, selected_id))
                        cursor.execute("""INSERT INTO download_links (ebook_id, download_url) VALUES (?, ?)
                                          ON CONFLICT(ebook_id) DO UPDATE SET download_url=excluded.download_url""",
                                       (selected_id, edit_dl))
                        conn.commit()
                        st.success(f"อัปเดตข้อมูลหนังสือ ID #{selected_id} เรียบร้อย!")
                        st.rerun()

        # 3. เปิด/ปิด หรือ ลบการจำหน่าย
        elif action == "❌ เปิด/ปิด การจำหน่าย":
            ebook_list = ebooks_all['ebook_id'].tolist()
            if ebook_list:
                selected_id = st.selectbox("เลือก ID หนังสือ", ebook_list, key="toggle_select")
                target = pd.read_sql_query("SELECT title, is_active FROM ebooks WHERE ebook_id = ?", conn, params=[selected_id]).iloc[0]
                
                current_status = "กำลังจำหน่าย" if target['is_active'] == 1 else "ถูกซ่อน (ปิดการขาย)"
                st.write(f"หนังสือ: **{target['title']}** (สถานะปัจจุบัน: {current_status})")
                
                c_btn1, c_btn2 = st.columns(2)
                if target['is_active'] == 1:
                    if c_btn1.button("🚫 ซ่อนหนังสือจากหน้าร้าน", type="primary"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE ebooks SET is_active = 0 WHERE ebook_id = ?", (selected_id,))
                        conn.commit()
                        st.success("ซ่อนหนังสือเรียบร้อยแล้ว!")
                        st.rerun()
                else:
                    if c_btn2.button("✅ เปิดวางจำหน่ายอีกครั้ง"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE ebooks SET is_active = 1 WHERE ebook_id = ?", (selected_id,))
                        conn.commit()
                        st.success("เปิดวางจำหน่ายเรียบร้อยแล้ว!")
                        st.rerun()

    with tab3:
        st.subheader("จัดการและอนุมัติคำสั่งซื้อ")
        order_search = st.text_input("ค้นหาด้วย Order ID หรือชื่อลูกค้า")
        orders_query = """
            SELECT o.order_id, u.full_name, o.total_amount, o.status, p.payment_method,
                   p.payment_slip_url, o.created_at
            FROM orders o JOIN users u ON o.user_id = u.user_id
            LEFT JOIN payments p ON o.order_id = p.order_id
            WHERE 1=1
        """
        order_params = []
        if order_search.strip():
            orders_query += " AND (CAST(o.order_id AS TEXT) LIKE ? OR u.full_name LIKE ?)"
            order_params.extend([f"%{order_search.strip()}%", f"%{order_search.strip()}%"])
        orders_query += " ORDER BY o.order_id DESC"
        orders_all = pd.read_sql_query(orders_query, conn, params=order_params)
        st.dataframe(orders_all.drop(columns=['payment_slip_url']), use_container_width=True)
        if not orders_all.empty:
            order_ids = orders_all['order_id'].astype(int).tolist()
        else:
            order_ids = []
        col_o1, col_o2 = st.columns(2)
        selected_oid = col_o1.selectbox("เลือกคำสั่งซื้อ", order_ids) if order_ids else None
        new_status = col_o2.selectbox("เปลี่ยนสถานะคำสั่งซื้อ", ['PENDING', 'PAID', 'CONFIRMED', 'CANCELLED'])
        
        if selected_oid is not None:
            detail = orders_all[orders_all['order_id'] == selected_oid].iloc[0]
            st.markdown(f"**รายละเอียด Order #{selected_oid}** — ลูกค้า: {detail['full_name']} — ยอดรวม: {detail['total_amount']:.2f} บาท")
            if pd.notna(detail['payment_method']):
                st.write(f"วิธีชำระเงิน: {detail['payment_method']}")
            proof = detail['payment_slip_url']
            if isinstance(proof, str) and proof.startswith('data:image/'):
                try:
                    image_bytes = base64.b64decode(proof.split(',', 1)[1])
                    st.image(image_bytes, caption="หลักฐานชำระเงินจำลอง", width=300)
                except (ValueError, IndexError):
                    st.warning("ไม่สามารถแสดงไฟล์หลักฐานนี้ได้")
            elif isinstance(proof, str) and proof.strip():
                st.markdown(f"[เปิดหลักฐานชำระเงิน]({proof})")
            detail_items = pd.read_sql_query("""
                SELECT e.title, oi.unit_price, oi.quantity, oi.unit_price * oi.quantity AS subtotal
                FROM order_items oi JOIN ebooks e ON oi.ebook_id=e.ebook_id
                WHERE oi.order_id=?
            """, conn, params=[int(selected_oid)])
            st.dataframe(detail_items, use_container_width=True)
            if st.button("อัปเดตสถานะคำสั่งซื้อ", disabled=not order_ids):
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, selected_oid))
                conn.commit()
                st.success(f"อัปเดตคำสั่งซื้อ #{selected_oid} เป็น {new_status} แล้ว")
                st.rerun()

    with tab4:
        st.subheader("🏷️ จัดการหมวดหมู่")
        cats_df = pd.read_sql_query("SELECT category_id, category_name FROM categories ORDER BY category_name", conn)
        with st.form("add_category_form"):
            category_new = st.text_input("ชื่อหมวดหมู่ใหม่")
            add_category_submit = st.form_submit_button("เพิ่มหมวดหมู่")
        if add_category_submit:
            if category_new.strip():
                try:
                    conn.execute("INSERT INTO categories (category_name) VALUES (?)", (category_new.strip(),))
                    conn.commit()
                    st.success("เพิ่มหมวดหมู่แล้ว")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("มีชื่อหมวดหมู่นี้แล้ว")
            else:
                st.warning("กรุณากรอกชื่อหมวดหมู่")
        if not cats_df.empty:
            selected_cat_id = st.selectbox("เลือกหมวดหมู่เพื่อแก้ไข", cats_df['category_id'].astype(int).tolist(), key="edit_category_id")
            cat_row = cats_df[cats_df['category_id'] == selected_cat_id].iloc[0]
            with st.form("edit_category_form"):
                category_edit = st.text_input("ชื่อหมวดหมู่", value=cat_row['category_name'])
                edit_category_submit = st.form_submit_button("บันทึกหมวดหมู่")
            if edit_category_submit:
                try:
                    conn.execute("UPDATE categories SET category_name=? WHERE category_id=?", (category_edit.strip(), selected_cat_id))
                    conn.commit()
                    st.success("แก้ไขหมวดหมู่แล้ว")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("ชื่อหมวดหมู่นี้ถูกใช้แล้ว")

    with tab5:
        st.subheader("รายชื่อสมาชิกและกำหนดบทบาท")
        users_df = pd.read_sql_query("SELECT u.user_id, u.full_name, u.email, u.role_id, r.role_name, u.created_at FROM users u JOIN roles r ON u.role_id=r.role_id ORDER BY u.user_id", conn)
        st.dataframe(users_df.drop(columns=['role_id']), use_container_width=True)
        role_rows = pd.read_sql_query("SELECT role_id, role_name FROM roles ORDER BY role_id", conn)
        role_map = dict(zip(role_rows['role_name'], role_rows['role_id']))
        if not users_df.empty:
            user_to_edit = st.selectbox("เลือกสมาชิก", users_df['user_id'].astype(int).tolist(), format_func=lambda uid: f"{uid} - {users_df.loc[users_df['user_id']==uid, 'full_name'].iloc[0]}")
            selected_user = users_df[users_df['user_id'] == user_to_edit].iloc[0]
            role_names = list(role_map.keys())
            current_role_index = role_names.index(selected_user['role_name']) if selected_user['role_name'] in role_names else 0
            chosen_role = st.selectbox("บทบาท", role_names, index=current_role_index)
            if st.button("บันทึกบทบาทผู้ใช้"):
                conn.execute("UPDATE users SET role_id=? WHERE user_id=?", (role_map[chosen_role], int(user_to_edit)))
                conn.commit()
                st.success("อัปเดตบทบาทผู้ใช้แล้ว")
                st.rerun()

    conn.close()

# ---------------------------------------------------------
# MAIN NAVIGATION ROUTER
# ---------------------------------------------------------
def main():
    st.sidebar.title("📖 E-Book Store")
    
    if st.session_state.user:
        st.sidebar.info(f"ผู้ใช้: **{st.session_state.user['name']}**\nสิทธิ์: **{st.session_state.user['role_name']}**")
        if st.sidebar.button("ออกจากระบบ"):
            st.session_state.user = None
            st.rerun()
    else:
        auth_mode = st.sidebar.radio("สมาชิก", ["เข้าสู่ระบบ", "สมัครสมาชิก"])
        if auth_mode == "เข้าสู่ระบบ": login()
        else: register()
        
    st.sidebar.divider()
    
    menu = ["📚 หน้าร้านค้า", "🛒 ตะกร้าสินค้า", "📦 ประวัติคำสั่งซื้อ"]
    if st.session_state.user and st.session_state.user['role_name'] == 'Customer':
        menu.append("👤 แก้ไขข้อมูลส่วนตัว")
    if st.session_state.user and st.session_state.user['role_name'] == 'Admin':
        menu.append("⚙️ หลังบ้าน (Admin)")
        
    choice = st.sidebar.selectbox("เมนูหลัก", menu)
    
    if choice == "📚 หน้าร้านค้า": render_storefront()
    elif choice == "🛒 ตะกร้าสินค้า": render_cart()
    elif choice == "📦 ประวัติคำสั่งซื้อ": render_my_orders()
    elif choice == "👤 แก้ไขข้อมูลส่วนตัว": render_profile()
    elif choice == "⚙️ หลังบ้าน (Admin)": render_admin_dashboard()

if __name__ == '__main__':
    main()