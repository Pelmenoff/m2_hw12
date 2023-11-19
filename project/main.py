from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from crud import (
    create_contact,
    get_contacts,
    get_contact_by_id,
    update_contact,
    delete_contact,
    search_contacts,
    upcoming_birthdays,
    create_user,
    get_user_by_email,
)
from database import SessionLocal
from datetime import datetime, timedelta
from models import (
    Contact,
    User,
    ContactCreate,
    ContactResponse,
    ContactListResponse,
    UserResponse,
)
from security import verify_password, get_password_hash


SECRET_KEY = "Pelmenoff"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db_user = get_user_by_email(db, email)
    if db_user is None:
        raise credentials_exception
    return db_user


@app.post("/contacts/", response_model=ContactResponse)
def create_new_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_contact(db, contact, current_user)


@app.get("/contacts/", response_model=ContactListResponse)
def get_all_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return {"contacts": get_contacts(db, skip=skip, limit=limit)}


@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    return get_contact_by_id(db, contact_id)


@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_existing_contact(
    contact_id: int, contact_data: ContactCreate, db: Session = Depends(get_db)
):
    return update_contact(db, contact_id, contact_data.dict())


@app.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_existing_contact(contact_id: int, db: Session = Depends(get_db)):
    return delete_contact(db, contact_id)


@app.get("/contacts/search/", response_model=ContactListResponse)
def search_contacts_api(
    query: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    return search_contacts(db, query, skip=skip, limit=limit)


@app.get("/contacts/upcoming_birthdays/", response_model=ContactListResponse)
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    return upcoming_birthdays(db)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return access_token


@app.post("/register/", response_model=UserResponse)
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=409, detail="User with this email already exists"
        )
    hashed_password = get_password_hash(password)
    return create_user(db, email=email, hashed_password=hashed_password)


@app.post("/token/")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    db_user = get_user_by_email(db, form_data.username)
    if db_user is None or not verify_password(
        form_data.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": form_data.username})
    refresh_token = create_refresh_token(data={"sub": form_data.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/token/refresh/")
def refresh_access_token(refresh_token: str = Depends(oauth2_scheme)):
    payload = verify_refresh_token(refresh_token)
    access_token = create_access_token(data={"sub": payload["sub"]})
    return {"access_token": access_token, "token_type": "bearer"}


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return refresh_token


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
