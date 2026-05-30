from sqlalchemy import Select, select, func
from sqlalchemy.orm import Session, joinedload

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt: Select[tuple[User]] = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def list_all(self) -> list[User]:
        stmt: Select[tuple[User]] = select(User).order_by(User.full_name.asc())
        return list(self.db.scalars(stmt).all())

    def list_by_department(self, department_id: int) -> list[User]:
        stmt: Select[tuple[User]] = (
            select(User)
            .where(User.department_id == department_id)
            .order_by(User.full_name.asc())
        )
        return list(self.db.scalars(stmt).all())

    def search(
        self, 
        search_query: str = "", 
        department_id: int | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[User], int]:
        """Search users by name or email with optional department filter."""
        stmt: Select[tuple[User]] = select(User).options(joinedload(User.department))
        
        if search_query:
            search_term = f"%{search_query}%"
            stmt = stmt.where(
                (User.full_name.ilike(search_term)) | (User.email.ilike(search_term))
            )
        
        if department_id is not None:
            stmt = stmt.where(User.department_id == department_id)
        
        # Count total matching records
        count_stmt = select(func.count()).select_from(User)
        if search_query:
            search_term = f"%{search_query}%"
            count_stmt = count_stmt.where(
                (User.full_name.ilike(search_term)) | (User.email.ilike(search_term))
            )
        if department_id is not None:
            count_stmt = count_stmt.where(User.department_id == department_id)
        
        total = self.db.scalar(count_stmt) or 0
        
        # Apply ordering and pagination
        stmt = stmt.order_by(User.full_name.asc()).offset(skip).limit(limit)
        
        users = list(self.db.scalars(stmt).all())
        return users, total

    def update(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
