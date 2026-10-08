import os
import time
import threading
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, CheckConstraint, update, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5433/course_db")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "10"))

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    max_capacity = Column(Integer, nullable=False)
    current_capacity = Column(Integer, nullable=False, default=0)
    __table_args__ = (
        CheckConstraint("current_capacity >= 0", name="ck_cap_nonneg"),
        CheckConstraint("current_capacity <= max_capacity", name="ck_cap_max"),
    )


def to_dict(c: Course) -> dict:
    return {"id": c.id, "name": c.name, "max_capacity": c.max_capacity,
            "current_capacity": c.current_capacity}


class CourseCreate(BaseModel):
    name: str = Field(min_length=1)
    max_capacity: int = Field(gt=0)


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    max_capacity: Optional[int] = Field(default=None, gt=0)


class TTLCache:
    def __init__(self, ttl: int):
        self.ttl, self._data, self._lock = ttl, {}, threading.Lock()

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item and item[0] > time.time():
                return item[1]
            self._data.pop(key, None)
            return None

    def set(self, key, value):
        with self._lock:
            self._data[key] = (time.time() + self.ttl, value)

    def clear(self):
        with self._lock:
            self._data.clear()


cache = TTLCache(CACHE_TTL)

app = FastAPI(title="Course Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(Course).first():
            db.add(Course(id=1, name="Analízis 1", max_capacity=2, current_capacity=0))
            db.add(Course(id=2, name="Programozás Alapjai", max_capacity=30, current_capacity=0))
            db.flush()
            if engine.dialect.name == "postgresql":
                db.execute(text(
                    "SELECT setval(pg_get_serial_sequence('courses', 'id'), (SELECT MAX(id) FROM courses))"
                ))
            db.commit()
    finally:
        db.close()


@app.get("/")
def read_index():
    return FileResponse("index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/courses")
def list_courses(db: Session = Depends(get_db)):
    cached = cache.get("all")
    if cached is not None:
        return cached
    result = [to_dict(c) for c in db.query(Course).order_by(Course.id).all()]
    cache.set("all", result)
    return result


@app.get("/api/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Kurzus nem található.")
    return to_dict(course)


@app.post("/api/courses", status_code=201)
def create_course(req: CourseCreate, db: Session = Depends(get_db)):
    course = Course(name=req.name, max_capacity=req.max_capacity, current_capacity=0)
    db.add(course)
    db.commit()
    db.refresh(course)
    cache.clear()
    return to_dict(course)


@app.put("/api/courses/{course_id}")
def update_course(course_id: int, req: CourseUpdate, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Kurzus nem található.")
    if req.name is not None:
        course.name = req.name
    if req.max_capacity is not None:
        if req.max_capacity < course.current_capacity:
            raise HTTPException(status_code=400, detail="A kapacitás nem lehet kisebb a jelenlegi létszámnál!")
        course.max_capacity = req.max_capacity
    db.commit()
    cache.clear()
    return to_dict(course)


@app.delete("/api/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Kurzus nem található.")
    if course.current_capacity > 0:
        raise HTTPException(
            status_code=400,
            detail="A kurzusnak van feliratkozott hallgatója, nem törölhető.",
        )
    db.delete(course)
    db.commit()
    cache.clear()
    return {"status": "success", "message": "Kurzus törölve."}


@app.post("/internal/courses/{course_id}/reserve")
def reserve_seat(course_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        update(Course)
        .where(Course.id == course_id, Course.current_capacity < Course.max_capacity)
        .values(current_capacity=Course.current_capacity + 1)
    )
    db.commit()
    if result.rowcount == 0:
        if not db.get(Course, course_id):
            raise HTTPException(status_code=404, detail="Kurzus nem található.")
        raise HTTPException(status_code=400, detail="Sikertelen tárgyfelvétel: A kurzus betelt!")
    cache.clear()
    course = db.get(Course, course_id)
    return {"status": "success", "course": to_dict(course)}


@app.post("/internal/courses/{course_id}/release")
def release_seat(course_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        update(Course)
        .where(Course.id == course_id, Course.current_capacity > 0)
        .values(current_capacity=Course.current_capacity - 1)
    )
    db.commit()
    if result.rowcount == 0:
        if not db.get(Course, course_id):
            raise HTTPException(status_code=404, detail="Kurzus nem található.")
        raise HTTPException(status_code=400, detail="Nincs mit felszabadítani.")
    cache.clear()
    course = db.get(Course, course_id)
    return {"status": "success", "course": to_dict(course)}
