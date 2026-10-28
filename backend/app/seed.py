import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Base, User, Team
from app.auth import hash_password

def seed_db():
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        if not db.query(User).filter(User.email == "admin@rhythmiq.io").first():
            db.add(User(
                id=str(uuid.uuid4()),
                email="admin@rhythmiq.io",
                name="Admin",
                password_hash=hash_password("admin123"),
                role="admin",
                timezone="UTC",
                created_at=datetime.utcnow(),
            ))

        if not db.query(Team).first():
            db.add(Team(
                id=str(uuid.uuid4()),
                name="My Team",
                created_at=datetime.utcnow(),
            ))

        db.commit()
        print("Seed complete: admin@rhythmiq.io / admin123")
    finally:
        db.close()
