import requests

# TEST REGISTER
res = requests.post("http://127.0.0.1:5000/register", json={
    "username": "testuser",
    "password": "123456"
})

print("Register:", res.json())

# TEST LOGIN
res = requests.post("http://127.0.0.1:5000/login", json={
    "username": "testuser",
    "password": "123456"
})

print("Login:", res.json())