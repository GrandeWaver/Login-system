import sqlite3
import config
import send_email
from random import randint

from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from passlib.hash import bcrypt

app = FastAPI()

SECRET = config.secret

templates = Jinja2Templates(directory="templates")

manager = LoginManager(SECRET, tokenUrl="/auth/login", use_cookie=True)
manager.cookie_name = config.cookie_name


@manager.user_loader
def load_user(username: str):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
            SELECT nickname, username, password
            FROM account
            WHERE username = ?
        """, (username,))

    user = cursor.fetchone()
    return user


def create_user(username: str, nickname: str, password: str):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute("""
               INSERT INTO account (username, password, nickname) VALUES (?, ?, ?)
           """, (username, password, nickname))
    except:
        return False
    connection.commit()
    return True


@app.post("/auth/login")
def login(request: Request, data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password

    user = load_user(username)

    if not user:
        resp = RedirectResponse(url="/*", status_code=status.HTTP_302_FOUND)
    elif not bcrypt.verify(password, user['password']):
        resp = templates.TemplateResponse("invalid_password.html",
                                          {"request": request, "nickname": user['nickname'], "email": user['username']})
    else:
        access_token = manager.create_access_token(
            data={"sub": username}
        )
        resp = RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
        manager.set_cookie(resp, access_token)
    return resp


@app.post("/auth/signup")
def signup(request: Request, username: str = Form(...), user_username: str = Form(...), password: str = Form(...)):
    username = username
    nickname = user_username
    password_hash = bcrypt.hash(password)

    create = create_user(username, nickname, password_hash)

    if not create:
        return {"Error": "can't create user"}
    else:
        range_start = 10 ** (5 - 1)
        range_end = (10 ** 5) - 1
        code = randint(range_start, range_end)
        code_hash = bcrypt.hash(str(code))

        connection = sqlite3.connect(config.DB_FILE)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("""UPDATE account set code = (?) WHERE username = (?)""", (code_hash, username))

        connection.commit()

        send_email.verification_code(username, code)
        return templates.TemplateResponse("confirm_email.html", {"request": request, "email": username})


@app.post("/confirm/email")
def reset_password(request: Request, username: str = Form(...), code: str = Form(...)):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
            SELECT code
            FROM account
            WHERE username = (?)
        """, (username,))

    code_db = cursor.fetchone()

    if bcrypt.verify(str(code), str(code_db['code'])):
        send_email.registered(username)
        return templates.TemplateResponse("signin_after_signup.html", {"request": request, "email": username})
    else:
        return templates.TemplateResponse("confirm_email_invalid.html", {"request": request, "email": username})


@app.get("/home")
def getPrivateendpoint(user=Depends(manager)):
    username = user["nickname"]

    return {"Welcome": username}


@app.get("/")
def loginwithCreds(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})


@app.get("/*")
def loginwithCreds(request: Request):
    return templates.TemplateResponse("invalid_signin.html", {"request": request})


@app.get("/signup")
def loginwithCreds(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/signup/*")
def loginwithCreds(request: Request):
    return templates.TemplateResponse("invalid_signup.html", {"request": request})


def change_password(in_email: str, in_password: str):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute("""
                UPDATE account set password = (?)
                WHERE username = (?)
            """, (in_password, in_email))
        send_email.changed_password(in_email)
    except:
        return False
    connection.commit()
    return True


@app.post("/change/password")
def change_password_site(request: Request, username: str = Form(...), password: str = Form(...)):
    password_hash = bcrypt.hash(password)
    change_password_function = change_password(username, password_hash)

    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
            SELECT nickname
            FROM account
            WHERE username = (?)
        """, (username,))
    nickname = cursor.fetchone()

    if change_password_function:
        return templates.TemplateResponse("confirmation.html", {"request": request, "email": username, "nickname": nickname['nickname']})
    else:
        return {"error": "can't change password"}


@app.post("/reset/password/code")
def reset_password(request: Request, username: str = Form(...), code: str = Form(...)):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
            SELECT code
            FROM account
            WHERE username = (?)
        """, (username,))

    code_db = cursor.fetchone()

    if bcrypt.verify(str(code), str(code_db['code'])):
        return templates.TemplateResponse("change_password.html", {"request": request, "email": username})
    else:
        return templates.TemplateResponse("change_password_invalid.html", {"request": request, "email": username})


@app.post("/reset/password/auth")
def send_code(request: Request, username: str = Form(...)):
    range_start = 10 ** (5 - 1)
    range_end = (10 ** 5) - 1
    code = randint(range_start, range_end)
    code_hash = bcrypt.hash(str(code))

    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""UPDATE account set code = (?) WHERE username = (?)""", (code_hash, username))

    connection.commit()

    send_email.verification_code(username, code)
    return templates.TemplateResponse("reset_password.html", {"request": request, "email": username})


def search_username(value: str):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT nickname FROM account
        where nickname like (?)
    """, (value, ))

    rows = cursor.fetchall()
    dictionary = list(rows)
    return dictionary


def search_email(value: str):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT username FROM account
        where username like (?)
    """, (value, ))

    rows = cursor.fetchall()
    dictionary = list(rows)
    return dictionary


@app.get('/auth/username/db/results')
def check_username(request: Request):
    q = request.query_params.get('q', False)
    result = search_username(q)
    return {'results': result}


@app.get('/auth/email/db/results')
def check_username(request: Request):
    q = request.query_params.get('q', False)
    result = search_email(q)
    return {'results': result}
