from typing import List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import (
    Favorite,
    Movie,
    MovieFile,
    MovieRequest,
    User,
    WatchHistory,
)
from bot.utils.code_generator import get_next_movie_code, is_code_available, sync_highest_code


class MovieService:
    """Kino katalogi va fayllar bilan ishlash bo'yicha asosiy xizmat."""

    @staticmethod
    async def get_by_code(session: AsyncSession, code: int) -> Optional[Movie]:
        """Kino kodi orqali qidirish va barcha qismlarini yuklash."""
        stmt = select(Movie).where(Movie.code == code, Movie.is_active.is_(True))
        return await session.scalar(stmt)

    @staticmethod
    async def get_by_id(session: AsyncSession, movie_id: int) -> Optional[Movie]:
        """ID orqali kinoni topish."""
        stmt = select(Movie).where(Movie.id == movie_id)
        return await session.scalar(stmt)

    @staticmethod
    async def create_movie(
        session: AsyncSession,
        title: str,
        genre: str,
        year: int,
        language: str,
        description: Optional[str],
        rating: float,
        video_file_id: str,
        poster_file_id: Optional[str] = None,
        custom_code: Optional[int] = None,
        duration: Optional[int] = None,
        file_size: Optional[int] = None,
        file_type: str = "video",
        quality: str = "HD",
    ) -> Movie:
        """Yangi kino va uning asosiy video faylini saqlash."""
        if custom_code is not None:
            if not await is_code_available(session, custom_code):
                raise ValueError(f"#{custom_code} kodi allaqachon mavjud!")
            movie_code = custom_code
            await sync_highest_code(session, movie_code)
        else:
            movie_code = await get_next_movie_code(session)

        movie = Movie(
            code=movie_code,
            title=title.strip(),
            genre=genre.strip(),
            year=year,
            language=language.strip(),
            description=description.strip() if description else None,
            rating=rating,
            poster_file_id=poster_file_id,
            is_active=True,
            views_count=0,
        )
        session.add(movie)
        await session.flush()

        # Asosiy video faylni saqlaymiz (1-qism)
        initial_file = MovieFile(
            movie_id=movie.id,
            file_id=video_file_id,
            part_number=1,
            part_name="1-qism",
            file_type=file_type,
            file_size=file_size,
            duration=duration,
            quality=quality,
        )
        session.add(initial_file)
        await session.flush()

        # Qayta yuklash
        return await MovieService.get_by_id(session, movie.id)  # type: ignore

    @staticmethod
    async def add_movie_part(
        session: AsyncSession,
        movie_id: int,
        file_id: str,
        part_number: int,
        part_name: Optional[str] = None,
        file_type: str = "video",
        file_size: Optional[int] = None,
        duration: Optional[int] = None,
        quality: str = "HD",
    ) -> MovieFile:
        """Mavjud kinoga yangi qism qo'shish."""
        movie = await MovieService.get_by_id(session, movie_id)
        if not movie:
            raise ValueError("Kino topilmadi!")

        part = MovieFile(
            movie_id=movie_id,
            file_id=file_id,
            part_number=part_number,
            part_name=part_name or f"{part_number}-qism",
            file_type=file_type,
            file_size=file_size,
            duration=duration,
            quality=quality,
        )
        session.add(part)
        await session.flush()
        return part

    @staticmethod
    async def delete_movie(session: AsyncSession, movie_id: int) -> bool:
        """Kinoni o'chirish."""
        movie = await MovieService.get_by_id(session, movie_id)
        if not movie:
            return False
        await session.delete(movie)
        await session.flush()
        return True

    @staticmethod
    async def update_movie(
        session: AsyncSession,
        movie_id: int,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        language: Optional[str] = None,
        description: Optional[str] = None,
        rating: Optional[float] = None,
    ) -> Optional[Movie]:
        """Kino parametrlarini yangilash."""
        movie = await MovieService.get_by_id(session, movie_id)
        if not movie:
            return None
        if title is not None:
            movie.title = title.strip()
        if genre is not None:
            movie.genre = genre.strip()
        if year is not None:
            movie.year = year
        if language is not None:
            movie.language = language.strip()
        if description is not None:
            movie.description = description.strip()
        if rating is not None:
            movie.rating = rating

        await session.flush()
        return movie

    @staticmethod
    async def record_movie_request(
        session: AsyncSession,
        query: str,
        user_id: Optional[int] = None,
        matched_movie_id: Optional[int] = None,
    ) -> None:
        """So'rovni jurnallashtirish va tomosha tarixiga kiritish."""
        req = MovieRequest(
            user_id=user_id,
            query=query,
            matched_movie_id=matched_movie_id,
        )
        session.add(req)

        if matched_movie_id:
            # Ko'rishlar sonini oshirish
            movie = await session.scalar(select(Movie).where(Movie.id == matched_movie_id))
            if movie:
                movie.views_count += 1

            if user_id:
                history = WatchHistory(user_id=user_id, movie_id=matched_movie_id)
                session.add(history)

        await session.flush()

    @staticmethod
    async def get_movies_paginated(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 6,
        order_by: str = "newest",
    ) -> Tuple[List[Movie], int]:
        """Kinolar ro'yxatini sahifalash bilan olish."""
        query = select(Movie).where(Movie.is_active.is_(True))

        if order_by == "popular":
            query = query.order_by(desc(Movie.views_count), desc(Movie.id))
        elif order_by == "code":
            query = query.order_by(Movie.code)
        else:  # newest
            query = query.order_by(desc(Movie.id))

        # Jami soni
        count_stmt = select(func.count(Movie.id)).where(Movie.is_active.is_(True))
        total_count = await session.scalar(count_stmt) or 0

        # Sahifa elementlari
        offset = (page - 1) * page_size
        items_stmt = query.offset(offset).limit(page_size)
        items = list(await session.scalars(items_stmt))

        return items, total_count

    @staticmethod
    async def get_random_movie(session: AsyncSession) -> Optional[Movie]:
        """Tasodifiy kino tanlash."""
        stmt = (
            select(Movie)
            .where(Movie.is_active.is_(True))
            .order_by(func.random())
            .limit(1)
        )
        return await session.scalar(stmt)

    @staticmethod
    async def search_movies(
        session: AsyncSession,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        page: int = 1,
        page_size: int = 6,
    ) -> Tuple[List[Movie], int]:
        """Nomi, janri yoki yili bo'yicha kinolarni qidirish."""
        stmt = select(Movie).where(Movie.is_active.is_(True))

        if query:
            clean_q = query.strip()
            # Agar raqam kiritilgan bo'lsa, kod yoki nom orqali
            if clean_q.isdigit():
                stmt = stmt.where(
                    (Movie.code == int(clean_q)) | (Movie.title.ilike(f"%{clean_q}%"))
                )
            else:
                stmt = stmt.where(Movie.title.ilike(f"%{clean_q}%"))

        if genre:
            stmt = stmt.where(Movie.genre.ilike(f"%{genre.strip()}%"))

        if year:
            stmt = stmt.where(Movie.year == year)

        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        # Paginated items
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(Movie.id)).offset(offset).limit(page_size)
        movies = list(await session.scalars(stmt))

        return movies, total

    @staticmethod
    async def get_all_genres(session: AsyncSession) -> List[str]:
        """Mavjud barcha janrlar ro'yxatini olish."""
        stmt = select(Movie.genre).where(Movie.is_active.is_(True)).distinct()
        raw_genres = await session.scalars(stmt)
        genres_set = set()
        for g in raw_genres:
            if g:
                for part in g.split(","):
                    p = part.strip()
                    if p:
                        genres_set.add(p.capitalize())
        return sorted(list(genres_set))

    # --- Sevimlilar (Favorites) ---

    @staticmethod
    async def is_favorite(session: AsyncSession, user_id: int, movie_id: int) -> bool:
        """Kino foydalanuvchining sevimlilarida bormi?"""
        stmt = select(Favorite).where(
            Favorite.user_id == user_id, Favorite.movie_id == movie_id
        )
        fav = await session.scalar(stmt)
        return fav is not None

    @staticmethod
    async def add_favorite(session: AsyncSession, user_id: int, movie_id: int) -> bool:
        """Kinoni sevimlilarga qo'shish."""
        if await MovieService.is_favorite(session, user_id, movie_id):
            return False
        session.add(Favorite(user_id=user_id, movie_id=movie_id))
        await session.flush()
        return True

    @staticmethod
    async def remove_favorite(session: AsyncSession, user_id: int, movie_id: int) -> bool:
        """Kinoni sevimlilardan o'chirish."""
        stmt = select(Favorite).where(
            Favorite.user_id == user_id, Favorite.movie_id == movie_id
        )
        fav = await session.scalar(stmt)
        if fav:
            await session.delete(fav)
            await session.flush()
            return True
        return False

    @staticmethod
    async def get_user_favorites(
        session: AsyncSession, user_id: int, page: int = 1, page_size: int = 6
    ) -> Tuple[List[Movie], int]:
        """Foydalanuvchining sevimli kinolari ro'yxati (sahifalash bilan)."""
        stmt = (
            select(Movie)
            .join(Favorite, Favorite.movie_id == Movie.id)
            .where(Favorite.user_id == user_id, Movie.is_active.is_(True))
            .order_by(desc(Favorite.created_at))
        )

        count_stmt = (
            select(func.count(Favorite.id))
            .join(Movie, Movie.id == Favorite.movie_id)
            .where(Favorite.user_id == user_id, Movie.is_active.is_(True))
        )
        total = await session.scalar(count_stmt) or 0

        offset = (page - 1) * page_size
        items = list(await session.scalars(stmt.offset(offset).limit(page_size)))
        return items, total
