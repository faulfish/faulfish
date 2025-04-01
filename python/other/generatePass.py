import random
import string

'''
使用Python, 自動生成一組密碼, 條件如下
(1) Use uppercase, lowercase and numbers characters.
(2) at least 8 characters in length.
(3) Can not include your account name in the password.
(4) Can not use any previously used/old passwords.
'''

# 已使用的舊密碼列表
old_passwords = ["oldpassword1", "oldpassword2", "oldpassword3"]  # 替換成你的舊密碼

# 你的帳戶名稱
account_name = "your_account_name"  # 替換成你的帳戶名稱

def generate_password():
    while True:
        # 生成一個隨機密碼
        password_length = random.randint(8, 16)  # 設定密碼長度範圍
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for _ in range(password_length))

        # 檢查密碼是否符合條件
        if (any(c.isdigit() for c in password) and
            any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            account_name not in password and
            password not in old_passwords):
            return password

# 生成密碼
new_password = generate_password()
print("Generated Password:", new_password)
