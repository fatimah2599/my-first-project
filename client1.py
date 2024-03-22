import socket

import gnupg
from cryptography.fernet import Fernet
import os



# دالة لإنشاء مفتاح PGP للعميل
def generate_pgp_key():
    gpg = gnupg.GPG()
    key_input_data = gpg.gen_key_input(
        name_email='client@example.com',
        passphrase='supersecretpassword'
    )
    key = gpg.gen_key(key_input_data)
    client_private_key = gpg.export_keys(key.fingerprint, True, passphrase='123')
    client_public_key = gpg.export_keys(key.fingerprint)
    return client_private_key, client_public_key

# باقي الكود كما هو
client_private_key_file = "client_private_key.txt"
client_public_key_file = "client_public_key.txt"

# تحقق من وجود ملفات المفتاح
if os.path.exists(client_private_key_file) and os.path.exists(client_public_key_file):
    with open(client_private_key_file, "r") as f:
        client_private_key = f.read()

    with open(client_public_key_file, "r") as f:
        client_public_key = f.read()
else:
    # إنشاء مفتاح جديد وحفظه في الملفات
    client_private_key, client_public_key = generate_pgp_key()
    with open(client_private_key_file, "w") as f:
        f.write(client_private_key)

    with open(client_public_key_file, "w") as f:
        f.write(client_public_key)

# باقي الكود كما هو


key_file_path = "symmetric_key.key"
if os.path.exists(key_file_path):
    with open(key_file_path, "rb") as key_file:
        symmetric_key = key_file.read()
else:
    print("Key file not found.")
    exit()
cipher_suite = Fernet(symmetric_key)
server_ip = "127.0.0.1"
server_port = 3306

# إذا كان الملف موجودًا، قراءة المفتاح منه
if os.path.exists(key_file_path):
    with open(key_file_path, "rb") as key_file:
        symmetric_key = key_file.read()
else:
    print("Key file not found.")
    exit()




client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_ip, server_port))


with open("client_public_key.txt", "r") as key_file:
    client_public_key = key_file.read()

# إرسال مفتاح العميل العام إلى الخادم
client_socket.send(client_public_key.encode())


# استقبال مفتاح الخادم العام
server_public_key = client_socket.recv(4096).decode()
print("Received Server Public Key:", server_public_key)
with open("server_public_key_received.txt", "w") as key_file:
    key_file.write(server_public_key)
# قد تحتاج إلى استخدام مفتاح الخادم العام في الخطوات التالية
# أغلق الاتصال

gpg = gnupg.GPG()
# توليد مفتاح جلسة
session_key = gpg.gen_key_input(passphrase='sessionpassphrase')
session_key = gpg.gen_key(session_key)

# تشفير مفتاح الجلسة وإرساله إلى الخادم
encrypted_session_key = gpg.encrypt(str(session_key), 'server@example.com')
client_socket.send(str(encrypted_session_key).encode())
print("ok")
# استقبال موافقة على مفتاح الجلسة من الخادم
response = client_socket.recv(1024).decode()
print(response.decode())
print("ok2")



def choose_action():
    print("Choose action:")
    print("1. Create an account")
    print("2. Log in first time")
    print("3. Log in ")

    choice = input("Enter the number of your choice: ")

    if choice == "1":
        username = input("Enter your desired username: ")
        password = input("Enter your password: ")
        role = input("press 1 if you are student , press 2 if you are professor: ")
        create_account(username, password, role)
    elif choice == "2":
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        login(username, password)
    elif choice == "3":
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        login_last(username, password)
    else:
        print("Invalid choice. Please enter 1 or 2.")
        choose_action()


def login(username, password):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_ip, server_port))

        request = f"login;{username};{password}"
        encrypted_request = cipher_suite.encrypt(request.encode())
        client_socket.send(encrypted_request)
        encrypted_response = client_socket.recv(1024)
        response = encrypted_response.decode()
        if response == "SUCCESS: Login successful.":
            update_account(username, password)
        else:
            print(response)


def login_last(username, password):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_ip, server_port))

        request = f"login;{username};{password}"
        encrypted_request = cipher_suite.encrypt(request.encode())
        client_socket.send(encrypted_request)
        encrypted_response = client_socket.recv(1024)
        response = encrypted_response.decode()
        print(response)


def update_account(username, password):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_ip, server_port))
        national_id = input("Enter your national_id: ")
        phone_number = input("Enter your phone_number: ")
        address = input("Enter your address: ")
        request = f"update_account;{username};{password};{national_id};{phone_number};{address}"
        print(request)
        encrypted_request = cipher_suite.encrypt(request.encode())
        client_socket.send(encrypted_request)
        encrypted_response = client_socket.recv(1024)
        response = encrypted_response.decode()
        print(response)


def create_account(username, password, role):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_ip, server_port))

        request = f"create_account;{username};{password};{role}"
        encrypted_request = cipher_suite.encrypt(request.encode())
        client_socket.send(encrypted_request)
        encrypted_response = client_socket.recv(1024)
        response = encrypted_response.decode()
        print(response)

choose_action()