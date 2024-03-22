import socket
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import threading

import gnupg
import pymysql
from cryptography.fernet import Fernet
import os



# دالة لإنشاء مفتاح جديد PGP
def generate_pgp_key():
    gpg = gnupg.GPG()
    key_input_data = gpg.gen_key_input(
        name_email='server@example.com',
        passphrase='supersecretpassword',
        key_type="RSA",  # نوع المفتاح المراد إنشاؤه
        key_length=2048  # طول المفتاح
    )
    key = gpg.gen_key(key_input_data)
    server_private_key = gpg.export_keys(key.fingerprint, True, passphrase='supersecretpassword')
    server_public_key = gpg.export_keys(key.fingerprint)
    return server_private_key, server_public_key


server_private_key, server_public_key = generate_pgp_key()
# يمكنك تخزين server_public_key في قاعدة البيانات

# باقي الكود كما هو

key_file_path = "symmetric_key.key"
# إذا كان الملف موجودًا، قراءة المفتاح منه
if os.path.exists(key_file_path):
    with open(key_file_path, "rb") as key_file:
        symmetric_key = key_file.read()
else:
    # إنشاء مفتاح جديد وحفظه في الملف
    symmetric_key = Fernet.generate_key()
    with open(key_file_path, "wb") as key_file:
        key_file.write(symmetric_key)

cipher_suite = Fernet(symmetric_key)

server_private_key_file = "server_private_key.txt"
server_public_key_file = "server_public_key.txt"

# تحقق من وجود ملفات المفتاح
if os.path.exists(server_private_key_file) and os.path.exists(server_public_key_file):
    with open(server_private_key_file, "r") as f:
        server_private_key = f.read()

    with open(server_public_key_file, "r") as f:
        server_public_key = f.read()
else:
    # إنشاء مفتاح جديد وحفظه في الملفات
    server_private_key, server_public_key = generate_pgp_key()
    with open(server_private_key_file, "w") as f:
        f.write(server_private_key)

    with open(server_public_key_file, "w") as f:
        f.write(server_public_key)

#handchecking :server is sending

with open("server_public_key.txt", "r") as key_file:
    server_public_key = key_file.read()
    print("Server Public Key:", server_public_key)




server_ip = "127.0.0.1"
server_port = 3306
db_server = "localhost"
db_user = "root"
db_password = ""
db_name = "iss"


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_ip, server_port))
server_socket.listen(1)

print(f"Server listening on {server_ip}:{server_port}")

client_socket, client_addr = server_socket.accept()

# إرسال مفتاح الخادم العام إلى العميل
client_socket.send(server_public_key.encode())

client_public_key = client_socket.recv(4096).decode()
print("Received Client Public Key:", client_public_key)

# حفظ مفتاح العميل العام في ملف
with open("client_public_key_received.txt", "w") as key_file:
    key_file.write(client_public_key)



# أغلق الاتصال
client_socket.close()
server_socket.close()




def connect_to_database():
    return pymysql.connect(user=db_user, password=db_password, database=db_name)


def login(client_socket, username, password):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # تحقق من وجود المستخدم في قاعدة البيانات
        query_check_user = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cursor.execute(query_check_user)
        existing_user = cursor.fetchone()

        if existing_user:
            client_socket.send("SUCCESS: Login successful.".encode())
        else:
            client_socket.send("FAILURE: Invalid username or password.".encode())

    except Exception as e:
        print(f"Database error: {e}")
        client_socket.send("FAILURE: Database error.".encode())

    finally:
        if conn:
            conn.close()


def login_last(client_socket, username, password):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # تحقق من وجود المستخدم في قاعدة البيانات
        query_check_user = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cursor.execute(query_check_user)
        existing_user = cursor.fetchone()

        if existing_user:
            client_socket.send("SUCCESS: Login successful.".encode())
        else:
            client_socket.send("FAILURE: Invalid username or password.".encode())

    except Exception as e:
        print(f"Database error: {e}")
        client_socket.send("FAILURE: Database error.".encode())

    finally:
        if conn:
            conn.close()


def create_account(client_socket, username, password, role):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # قم بالتحقق من وجود المستخدم في قاعدة البيانات
        query_check_user = f"SELECT * FROM users WHERE username='{username}'"
        cursor.execute(query_check_user)
        existing_user = cursor.fetchone()

        if existing_user:
            client_socket.send("FAILURE: Username already exists.".encode())
        else:
            # قم بإضافة المستخدم إلى قاعدة البيانات إذا لم يكن موجودًا
            query_create_user = f"INSERT INTO users (username, password ,role) VALUES ('{username}', '{password}','{role}')"
            cursor.execute(query_create_user)
            conn.commit()
            client_socket.send("SUCCESS: Account created successfully.".encode())

    except Exception as e:
        print(f"Database error: {e}")
        client_socket.send("FAILURE: Database error".encode())

    finally:
        if conn:
            conn.close()


def update_account(client_socket, username, password, national_id, phone_number, address):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # تحقق من وجود المستخدم في قاعدة البيانات
        query_check_user = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cursor.execute(query_check_user)
        existing_user = cursor.fetchone()

        if existing_user:
            query_update_user = f"UPDATE users SET national_id='{national_id}', phone_number='{phone_number}', address='{address}' WHERE username='{username}' AND password='{password}'"
            cursor.execute(query_update_user)
            conn.commit()
            client_socket.send("SUCCESS: Account completed successfully.".encode())
    except Exception as e:
        print(f"Database error: {e}")
        client_socket.send("FAILURE: Database error.".encode())

    finally:
        if conn:
            conn.close()


def handle_client(client_socket):
    encrypted_request = client_socket.recv(1024)
    decrypted_request = cipher_suite.decrypt(encrypted_request).decode('utf-8')

    print("Encrypted data after receiving:", encrypted_request)
    print("Received data:", decrypted_request)

    request = decrypted_request.split(";")

    if request[0] == "create_account":
        create_account(client_socket, request[1], request[2], request[3])
    elif request[0] == "login":
        login(client_socket, request[1], request[2])
    elif request[0] == "login_last":
        login_last(client_socket, request[1], request[2])
    elif request[0] == "update_account":
        update_account(client_socket, request[1], request[2], request[3], request[4], request[5])

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"Server listening on {server_ip}:{server_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")

        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()


start_server()