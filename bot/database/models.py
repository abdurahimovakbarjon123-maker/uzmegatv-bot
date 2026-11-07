from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base, utc_now


class User(Base):
    """Foydalanuvchilar modeli (Telegram users)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )

    # Aloqalar
    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan"
    )
    watch_history: Mapped[List["WatchHistory"]] = relationship(
        "WatchHistory", back_populates="user", cascade="all, delete-orphan"
    )
    requests: Mapped[List["MovieRequest"]] = relationship(
        "MovieRequest", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} username={self.username}>"


class Movie(Base):
    """Kinolar modeli (Movie records)."""
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    original_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    genre: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(64), default="O‘zbekcha", index=True, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    poster_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )

    # Aloqalar
    files: Mapped[List["MovieFile"]] = relationship(
        "MovieFile",
        back_populates="movie",
        cascade="all, delete-orphan",
        order_by="MovieFile.part_number",
        lazy="selectin",
    )
    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite", back_populates="movie", cascade="all, delete-orphan"
    )
    watch_history: Mapped[List["WatchHistory"]] = relationship(
        "WatchHistory", back_populates="movie", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Movie code={self.code} title='{self.title}'>"


class MovieFile(Base):
    """Kino fayllari (qismlar, sifatlar va Telegram file_id lar)."""
    __tablename__ = "movie_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_unique_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    part_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    part_name: Mapped[Optional[str]] = mapped_column(String(100), default="1-qism", nullable=True)
    file_type: Mapped[str] = mapped_column(String(32), default="video", nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality: Mapped[Optional[str]] = mapped_column(String(32), default="HD", nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )

    # Aloqa
    movie: Mapped["Movie"] = relationship("Movie", back_populates="files")

    def __repr__(self) -> str:
        return f"<MovieFile movie_id={self.movie_id} part={self.part_number} file_id={self.file_id[:10]}...>"


class Favorite(Base):
    """Foydalanuvchilarning sevimli kinolari."""
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_favorite"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="favorites")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="favorites")


class WatchHistory(Base):
    """Kino ko'rish tarixi."""
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    watched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), index=True, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="watch_history")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="watch_history")


class RequiredChannel(Base):
    """Majburiy a'zo bo'linadigan Telegram kanallar."""
    __tablename__ = "required_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    invite_link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<RequiredChannel title='{self.title}' channel_id={self.channel_id}>"


class Admin(Base):
    """Bot administratorlari."""
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="admin", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Admin telegram_id={self.telegram_id} role={self.role}>"


class MovieRequest(Base):
    """Foydalanuvchi qidiruvlari va kino so'rovlari jurnali."""
    __tablename__ = "movie_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    matched_movie_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), index=True, nullable=False
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="requests")


class BotSetting(Base):
    """Botning dinamik sozlamalari (DB da saqlanadigan kalit-qiymatlar)."""
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BotSetting key='{self.key}' value='{self.value}'>"


class Broadcast(Base):
    """Xabar yuborish tarixi va statistikasi."""
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_type: Mapped[str] = mapped_column(String(32), default="text", nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
