import logging
from datetime import datetime, timedelta
import uuid
import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext


from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Auth():
    hasher = CryptContext(schemes=['bcrypt'])
    secret = JWT_SECRET_KEY

    def encode_password(self, password):
        return self.hasher.hash(password)

    def verify_password(self, password, encoded_password):
        return self.hasher.verify(password, encoded_password)

    def encode_token(self, username):
        logger.debug('encode_token')
        payload = {
            'exp': datetime.utcnow() + timedelta(days=0, minutes=30),
            'iat': datetime.utcnow(),
            'scope': 'access_token',
            'sub': username,
            'jti': str(uuid.uuid4())
        }
        return jwt.encode(
            payload,
            self.secret,
            algorithm=JWT_ALGORITHM
        )

    def decode_token(self, token):
        logger.debug('decode_token')
        try:
            payload = jwt.decode(token, self.secret, algorithms=[JWT_ALGORITHM])
            if (payload['scope'] == 'access_token'):
                return payload
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Scope for the token is invalid')
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token expired: {}'.format(e.args))
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

    def encode_refresh_token(self, username):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=0, hours=10),
            'iat': datetime.utcnow(),
            'scope': 'refresh_token',
            'sub': username,
            'jti': str(uuid.uuid4())
        }
        return jwt.encode(
            payload,
            self.secret,
            algorithm=JWT_ALGORITHM
        )
    
    def decode_refresh_token(self, token):
        logger.debug('decode_refresh_token')
        try:
            payload = jwt.decode(token, self.secret, algorithms=[JWT_ALGORITHM])
            if (payload['scope'] == 'refresh_token'):
                return payload
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Scope for the token is invalid')
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token expired: {}'.format(e.args))
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

    def update_refresh_token(self, refresh_token):
        logger.debug('update_refresh_token')
        try:
            payload = jwt.decode(refresh_token, self.secret, algorithms=[JWT_ALGORITHM])
            logger.debug(payload['scope'])
            if (payload['scope'] == 'refresh_token'):
                username = payload['sub']
                new_token = self.encode_refresh_token(username)
                return new_token
            raise HTTPException(status_code=401, detail='Invalid scope for token')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Refresh token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid refresh token')

    def update_access_token(self, access_token):
        logger.debug('update_access_token')
        try:
            payload = jwt.decode(access_token, self.secret, algorithms=[JWT_ALGORITHM])
            logger.debug(payload['scope'])
            if (payload['scope'] == 'access_token'):
                username = payload['sub']
                new_token = self.encode_token(username)
                return new_token
            raise HTTPException(status_code=401, detail='Invalid scope for token')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Refresh token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid refresh token')
