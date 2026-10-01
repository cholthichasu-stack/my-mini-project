import sqlite3
import hashlib

def init_database():
    conn = sqlite3.connect('ebook_store.db')
    cursor = conn.cursor()
    
    # เปิดใช้งาน WAL Mode
    cursor.execute('PRAGMA journal_mode=WAL;')
    
    # สร้างตารางบทบาท (roles)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT UNIQUE NOT NULL
    );
    ''')

    # สร้างตารางผู้ใช้ (users)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role_id INTEGER NOT NULL,
        FOREIGN KEY (role_id) REFERENCES roles (role_id)
    );
    ''')

    # สร้างตารางหมวดหมู่ (categories)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL
    );
    ''')

    # สร้างตารางผู้แต่ง (authors)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authors (
        author_id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name TEXT NOT NULL
    );
    ''')

    # สร้างตารางหนังสือ (ebooks)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ebooks (
        ebook_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author_id INTEGER,
        category_id INTEGER,
        price REAL NOT NULL,
        description TEXT,
        cover_image_url TEXT,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (author_id) REFERENCES authors (author_id),
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
    );
    ''')

    # สร้างตารางคำสั่งซื้อ (orders)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
    ''')

    # สร้างตารางรายการสินค้าในคำสั่งซื้อ (order_items)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        ebook_id INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (ebook_id) REFERENCES ebooks (ebook_id)
    );
    ''')

    # สร้างตารางการชำระเงิน (payments)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        payment_method TEXT NOT NULL,
        payment_slip_url TEXT,
        paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
    );
    ''')

    # ใส่ข้อมูลเริ่มต้น (Sample Data)
    cursor.execute("INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (1, 'Admin'), (2, 'Customer');")
    cursor.execute("INSERT OR IGNORE INTO categories (category_name) VALUES ('Programming'), ('Business'), ('Fiction');")
    cursor.execute("INSERT OR IGNORE INTO authors (author_name) VALUES ('John Doe'), ('Jane Smith');")
    
    # เพิ่มแอดมินตัวอย่าง (password: admin123)
    admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("INSERT OR IGNORE INTO users (email, full_name, password_hash, role_id) VALUES ('admin@ebook.com', 'Admin User', ?, 1);", (admin_pass,))

    # เพิ่มหนังสือตัวอย่าง
    cursor.execute("INSERT OR IGNORE INTO ebooks (title, author_id, category_id, price, description) VALUES ('Python Web Development', 1, 1, 299.0, 'Learn Streamlit and SQLite');")

    conn.commit()
    conn.close()
    print("สร้างฐานข้อมูล ebook_store.db พร้อมข้อมูลตัวอย่างเรียบร้อยแล้ว!")

if __name__ == '__main__':
    init_database()