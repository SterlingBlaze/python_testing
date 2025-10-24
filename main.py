from typing import Optional, List
from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
# from passlib.context import CryptContext
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, get_db
from cryptography.fernet import Fernet
from datetime import datetime

# pwd_context= CryptContext(schemes=["bcrypt"], deprecated="auto")
key = Fernet.generate_key()
f = Fernet(key)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


while True:
    try:
        conn = psycopg2.connect(host='localhost', database='fastapi1',user='postgres',
                                password='superpassword',cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print('database connected')
        break
    except Exception as error:
        print('Connection failed!')
        print(f'Error: {error}')
        time.sleep(5)


my_posts = [{"title": "new_title", "content": "new_content", "id": 1},
             {"title":"favorite food","content":"pizza","id":2}]

def find_post(id):
    for p in my_posts:
        if p["id"]== id:
            return p

def find_index_post(id):
    for i, p in enumerate(my_posts):
        if p['id'] == id:
            return i

@app.get("/")        #------------------------decorater used for fastapi
def root():          #------------------------async is optional(api call, database communication), root can be named anything like "login_user"
    return {"Hello": "you have reached root"}


@app.get("/posts", response_model=List[schemas.Post])
def get_posts(db: Session= Depends(get_db)):
    # cursor.execute("""SELECT * FROM posts""")
    # posts= cursor.fetchall()
    posts= db.query(models.Post).all()
    return posts

@app.post("/posts", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(post: schemas.PostCreate, db: Session= Depends(get_db)):  
   # data is not directly put instead sanitised first("%S") to avoid potential sql injection attacks
    # cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s,%s,%s) 
    #                RETURNING * """,
    #                     (post.title,post.content,post.published))
    # new_post= cursor.fetchone()
    # conn.commit()
    # print(**post.model_dump())
    # title=post.title, content=post.content, published=post.published
    new_post= models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


#latest post *Note paths should be in order to avoid incorrect requests 
@app.get("/posts/latest")
def latest_get_post():
    post = my_posts[len(my_posts)-1]
    return {"details": post}

#get specific post id
@app.get("/posts/{id}", response_model=schemas.Post) 
def get_post(id: int, db: Session= Depends(get_db)):  #----- ":int" makes sure id is int only
    # cursor.execute("""SELECT * FROM posts WHERE id = %s """,(str(id)))
    # post = cursor.fetchone()
    post= db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} not found")
        # response.status_code = status.HTTP_404_NOT_FOUND
        # return {"message": f"post with id-{id} not found"}
    return post


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT,)
def delete_post(id: int, db: Session= Depends(get_db)): 
    # cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING * """, (str(id)))
    # deleted_post= cursor.fetchone()
    # conn.commit()
    post_query = db.query(models.Post).filter(models.Post.id == id)
    if post_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"post with id: {id} does not exist")
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

@app.put("/posts/{id}",response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session= Depends(get_db)):
    # cursor.execute("""UPDATE posts SET title = %s, content =%s, published= %s WHERE id = %s RETURNING *""",
    # (post.title, post.content, post.published, str(id)))
    # updated_post=cursor.fetchone()
    # conn.commit()
    post_query= db.query(models.Post).filter(models.Post.id == id)
    post= post_query.first()
    if post == None:#find index of id
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} does not exist")
    # print(updated_post.model_dump())
    post_query.update(updated_post.model_dump(), synchronize_session=False)
    db.commit()

    return post_query.first()
    

#-----------------------------------------------------------------------------------------------------------------------------------------------------


@app.post("/users", status_code=status.HTTP_201_CREATED, 
          response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session= Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    # print("user",existing_user)
    # 2. If user exists, raise an informative error
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User with email {user.email} already exists.")

    password = user.password
    encoded_password = password.encode()  # Passwords must be in bytes
    encrypted_password = f.encrypt(encoded_password)
    user.password= encrypted_password
# add user
    new_user= models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

