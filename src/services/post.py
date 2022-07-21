import json
import logging
from functools import lru_cache
from typing import Optional

from fastapi import Depends
from sqlmodel import Session

from src.api.v1.schemas import PostCreate, PostModel
from src.db import AbstractCache, get_cache, get_session
from src.models import Post
from src.services import ServiceMixin

__all__ = ("PostService", "get_post_service")


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PostService(ServiceMixin):
    def get_post_list(self) -> dict:
        """Получить список постов."""
        posts = []
        for key in self.cache.cache.keys("post*"):
            posts.append(json.loads(self.cache.get(key=key)))
        if not posts:
            posts = self.session.query(Post).order_by(Post.created_at).all()
            return {"posts": [PostModel(**post.dict()) for post in posts]}
        else:
            logger.debug('Got list of posts from redis cache.')
            return {"posts": [PostModel(**post) for post in posts]}
        

    def get_post_detail(self, item_id: int) -> Optional[dict]:
        """Получить детальную информацию поста."""
        if cached_post := self.cache.get(key=f"post{item_id}"):
            logger.debug('Load post from redis cache.')
            return json.loads(cached_post)

        post = self.session.query(Post).filter(Post.id == item_id).first()
        if post:
            self.cache.set(key=f"{post.id}", value=post.json())
        return post.dict() if post else None

    def create_post(self, post: PostCreate) -> dict:
        """Создать пост."""
        new_post = Post(title=post.title, description=post.description)
        self.session.add(new_post)
        self.session.commit()
        self.session.refresh(new_post)
        new_post_dict = new_post.dict()
        new_post_dict['created_at'] = new_post_dict['created_at'].strftime('%Y-%m-%dT%H:%M:%S')
        self.cache.set(key=f"post{new_post.id}", value=json.dumps(new_post_dict))
        return new_post_dict


# get_post_service — это провайдер PostService. Синглтон
@lru_cache()
def get_post_service(
    cache: AbstractCache = Depends(get_cache),
    session: Session = Depends(get_session),
) -> PostService:
    return PostService(cache=cache, session=session)
