"""Initial UZMEGATV schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-06 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("first_name", sa.String(length=128), nullable=True),
        sa.Column("last_name", sa.String(length=128), nullable=True),
        sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=True)

    # 2. movies
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("original_title", sa.String(length=255), nullable=True),
        sa.Column("genre", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=64), server_default="O‘zbekcha", nullable=False),
        sa.Column("rating", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("poster_file_id", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("views_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_movies_code"), "movies", ["code"], unique=True)
    op.create_index(op.f("ix_movies_title"), "movies", ["title"], unique=False)
    op.create_index(op.f("ix_movies_genre"), "movies", ["genre"], unique=False)
    op.create_index(op.f("ix_movies_year"), "movies", ["year"], unique=False)
    op.create_index(op.f("ix_movies_is_active"), "movies", ["is_active"], unique=False)

    # 3. movie_files
    op.create_table(
        "movie_files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.String(length=255), nullable=False),
        sa.Column("file_unique_id", sa.String(length=255), nullable=True),
        sa.Column("part_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("part_name", sa.String(length=100), server_default="1-qism", nullable=True),
        sa.Column("file_type", sa.String(length=32), server_default="video", nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("quality", sa.String(length=32), server_default="HD", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_movie_files_movie_id"), "movie_files", ["movie_id"], unique=False)

    # 4. favorites
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_user_movie_favorite"),
    )
    op.create_index(op.f("ix_favorites_user_id"), "favorites", ["user_id"], unique=False)
    op.create_index(op.f("ix_favorites_movie_id"), "favorites", ["movie_id"], unique=False)

    # 5. watch_history
    op.create_table(
        "watch_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("watched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_watch_history_user_id"), "watch_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_watch_history_movie_id"), "watch_history", ["movie_id"], unique=False)
    op.create_index(op.f("ix_watch_history_watched_at"), "watch_history", ["watched_at"], unique=False)

    # 6. required_channels
    op.create_table(
        "required_channels",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("invite_link", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_id"),
    )

    # 7. admins
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("full_name", sa.String(length=128), nullable=True),
        sa.Column("role", sa.String(length=32), server_default="admin", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admins_telegram_id"), "admins", ["telegram_id"], unique=True)

    # 8. movie_requests
    op.create_table(
        "movie_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("matched_movie_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["matched_movie_id"], ["movies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_movie_requests_user_id"), "movie_requests", ["user_id"], unique=False)
    op.create_index(op.f("ix_movie_requests_created_at"), "movie_requests", ["created_at"], unique=False)

    # 9. bot_settings
    op.create_table(
        "bot_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bot_settings_key"), "bot_settings", ["key"], unique=True)

    # 10. broadcasts
    op.create_table(
        "broadcasts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("message_type", sa.String(length=32), server_default="text", nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("file_id", sa.String(length=255), nullable=True),
        sa.Column("total_users", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sent_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("broadcasts")
    op.drop_table("bot_settings")
    op.drop_table("movie_requests")
    op.drop_table("admins")
    op.drop_table("required_channels")
    op.drop_table("watch_history")
    op.drop_table("favorites")
    op.drop_table("movie_files")
    op.drop_table("movies")
    op.drop_table("users")
