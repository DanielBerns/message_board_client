import aiohttp
import yaml
import logging
from typing import List, Dict, Any, Optional, Type
from types import TracebackType
from cryptography.fernet import Fernet, InvalidToken

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

class MessageBoardClient:
    def __init__(self, config_path: str) -> None:
        """Initializes the client, reads credentials, and sets up encryption."""
        with open(config_path, 'r') as file:
            config: Dict[str, Any] = yaml.safe_load(file)

        self.base_url: str = config['server']['base_url'].rstrip('/')
        self.username: str = config['credentials']['username']
        self.password: str = config['credentials']['password']

        shared_key = config.get('encryption', {}).get('shared_key')
        if not shared_key:
            raise ValueError("Encryption key missing from configuration.")
        self.cipher: Fernet = Fernet(shared_key.encode())

        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    async def __aenter__(self) -> 'SecureMessageBoardClient':
        """Allows usage in an async context manager."""
        self.session = aiohttp.ClientSession()
        await self.login()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Ensures the session is closed when exiting the context."""
        if self.session:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Internal helper to make requests and inject the JWT Bearer token."""
        if not self.session:
            raise RuntimeError("Session is not initialized. Use async with context manager.")

        url: str = f"{self.base_url}{endpoint}"
        headers: Dict[str, str] = kwargs.pop('headers', {})

        if self.access_token and not endpoint.startswith('/auth/login'):
            headers['Authorization'] = f"Bearer {self.access_token}"

        headers['Content-Type'] = 'application/json'

        async with self.session.request(method, url, headers=headers, **kwargs) as response:
            if response.status in (401, 403) and endpoint != '/auth/refresh':
                logger.warning("Token might be expired. Attempting refresh...")
                if await self.refresh_access_token():
                    headers['Authorization'] = f"Bearer {self.access_token}"
                    async with self.session.request(method, url, headers=headers, **kwargs) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json() if retry_resp.content_type == 'application/json' else await retry_resp.text()

            response.raise_for_status()
            return await response.json() if response.content_type == 'application/json' else await response.text()

    # --- Authentication ---

    async def login(self) -> None:
        """Endpoint: POST /auth/login"""
        payload: Dict[str, str] = {"username": self.username, "password": self.password}
        data: Dict[str, Any] = await self._request('POST', '/auth/login', json=payload)
        self.access_token = data.get('access_token')
        self.refresh_token = data.get('refresh_token')
        logger.info(f"Successfully logged in as {self.username}")

    async def refresh_access_token(self) -> bool:
        """Endpoint: POST /auth/refresh"""
        if not self.refresh_token:
            return False

        headers: Dict[str, str] = {'Authorization': f"Bearer {self.refresh_token}"}
        try:
            data: Dict[str, Any] = await self._request('POST', '/auth/refresh', headers=headers)
            self.access_token = data.get('access_token')
            return True
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return False

    async def logout(self) -> None:
        """Endpoint: POST /auth/logout"""
        await self._request('POST', '/auth/logout')
        self.access_token = None
        self.refresh_token = None
        logger.info("Logged out successfully.")

    # --- Encryption Helpers ---

    def _encrypt_content(self, content: str) -> str:
        """Encrypts a plaintext string into a base64 ciphertext string."""
        return self.cipher.encrypt(content.encode()).decode()

    def _decrypt_content(self, ciphertext: str) -> str:
        """Decrypts a base64 ciphertext string back to plaintext."""
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            return "[Decryption Failed: Invalid Key or Corrupted Data]"
        except Exception:
            return "[Decryption Failed: Unrecognized Format]"

    # --- Secure Messaging ---

    async def send_private_message(self, recipient: str, content: str) -> Any:
        """Endpoint: POST /api/messages/private"""
        encrypted_content: str = self._encrypt_content(content)
        payload: Dict[str, str] = {"recipient_username": recipient, "content": encrypted_content}
        return await self._request('POST', '/api/messages/private', json=payload)

    async def send_group_message(self, recipients: List[str], content: str) -> Any:
        """Endpoint: POST /api/messages/group"""
        encrypted_content: str = self._encrypt_content(content)
        payload: Dict[str, Any] = {"recipient_usernames": recipients, "content": encrypted_content}
        return await self._request('POST', '/api/messages/group', json=payload)

    async def send_public_message(self, tags: List[str], content: str) -> Any:
        """Endpoint: POST /api/messages/public"""
        encrypted_content: str = self._encrypt_content(content)
        payload: Dict[str, Any] = {"tags": tags, "content": encrypted_content}
        return await self._request('POST', '/api/messages/public', json=payload)

    async def get_private_messages(self) -> List[Dict[str, Any]]:
        """Endpoint: GET /api/messages/private"""
        messages: List[Dict[str, Any]] = await self._request('GET', '/api/messages/private')
        for msg in messages:
            if 'content' in msg:
                msg['content'] = self._decrypt_content(msg['content'])
        return messages

    async def get_group_messages(self) -> List[Dict[str, Any]]:
        """Endpoint: GET /api/messages/group"""
        messages: List[Dict[str, Any]] = await self._request('GET', '/api/messages/group')
        for msg in messages:
            if 'content' in msg:
                msg['content'] = self._decrypt_content(msg['content'])
        return messages

    async def get_public_messages(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Endpoint: GET /api/messages/public"""
        params: Dict[str, str] = {"tags": ",".join(tags)} if tags else {}
        messages: List[Dict[str, Any]] = await self._request('GET', '/api/messages/public', params=params)
        for msg in messages:
            if 'content' in msg:
                msg['content'] = self._decrypt_content(msg['content'])
        return messages

    async def delete_message(self, message_id: str) -> Any:
        """Endpoint: DELETE /api/messages/<message_id>"""
        return await self._request('DELETE', f'/api/messages/{message_id}')

    async def delete_all_messages(self) -> Any:
        """Endpoint: POST /api/messages/delete_all (Admin Only)"""
        payload: Dict[str, str] = {"confirmation": "delete all messages"}
        return await self._request('POST', '/api/messages/delete_all', json=payload)

    # --- Tag Subscriptions ---

    async def subscribe_tags(self, tags: List[str]) -> Any:
        """Endpoint: POST /api/tags/subscribe"""
        payload: Dict[str, List[str]] = {"tags": tags}
        return await self._request('POST', '/api/tags/subscribe', json=payload)

    async def unsubscribe_tags(self, tags: List[str]) -> Any:
        """Endpoint: POST /api/tags/unsubscribe"""
        payload: Dict[str, List[str]] = {"tags": tags}
        return await self._request('POST', '/api/tags/unsubscribe', json=payload)

    # --- Admin & Heartbeat ---

    async def get_server_status(self) -> Dict[str, Any]:
        """Endpoint: GET /api/admin/status (Admin Only)"""
        return await self._request('GET', '/api/admin/status')

    async def send_heartbeat(self) -> Any:
        """Endpoint: POST /api/heartbeat"""
        return await self._request('POST', '/api/heartbeat')

    async def get_heartbeats(self) -> Dict[str, Any]:
        """Endpoint: GET /api/heartbeat"""
        return await self._request('GET', '/api/heartbeat')
