from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="member")
    timezone = Column(String, default="UTC")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Team(Base):
    __tablename__ = "teams"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class UserTeam(Base):
    __tablename__ = "user_teams"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    team_id = Column(String, ForeignKey("teams.id"), primary_key=True)

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(String, primary_key=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    phone_number = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=True)
    status = Column(String, default="unknown")
    last_seen_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class ContactEvent(Base):
    __tablename__ = "contact_events"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    event_type = Column(String, nullable=False)
    event_subtype = Column(String, nullable=True)
    direction = Column(String, nullable=True)
    channel = Column(String, default="phone")
    event_time = Column(DateTime, nullable=False)
    response_latency_ms = Column(Integer, nullable=True)
    message_length = Column(Integer, nullable=True)
    message_mode = Column(String, nullable=True)
    task_context = Column(String, nullable=True)
    urgency_score = Column(Float, nullable=True)
    mood_label = Column(String, nullable=True)
    context_tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class StatePrediction(Base):
    __tablename__ = "state_predictions"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    predicted_state = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=True)
    evidence = Column(JSON, nullable=True)
    predicted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    prediction_id = Column(String, ForeignKey("state_predictions.id"), nullable=True)
    correct = Column(Boolean, nullable=False)
    user_label = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class FeatureHistory(Base):
    __tablename__ = "feature_history"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    feature_name = Column(String, nullable=False)
    feature_value = Column(Float, nullable=False)
    bucket_start = Column(DateTime, nullable=False)
    bucket_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(String, primary_key=True)
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    artifact_path = Column(String, nullable=True)
    trained_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class AppSetting(Base):
    __tablename__ = "app_settings"
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
