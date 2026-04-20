from sqlalchemy import Select, select
from sqlalchemy.orm import Session

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

    def update(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
