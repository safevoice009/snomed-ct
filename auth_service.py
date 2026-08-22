import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

logger = logging.getLogger("auth_service")

class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "doctor"

class SignInRequest(BaseModel):
    email: str
    password: str

class APIKeyCreateRequest(BaseModel):
    name: Optional[str] = "EMR Gateway Key"


class AuthService:
    """Manages user registration, session tokens, and dynamic B2B API keys using Supabase."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_client = None
        
        # Local fallback in-memory stores if Supabase is offline/mocked
        self._local_users: Dict[str, Dict[str, Any]] = {}
        self._local_accounts: Dict[str, str] = {} # email -> hashed password
        self._local_sessions: Dict[str, Dict[str, Any]] = {} # token -> session data
        self._local_api_keys: Dict[str, Dict[str, Any]] = {
            "test-dev-key": {"user_id": "usr_demo", "name": "Default Test Key", "is_active": True, "requests_count": 0}
        }
        
        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
                logger.info("AuthService connected to Supabase PostgreSQL.")
            except Exception as e:
                logger.error(f"AuthService failed to init Supabase client: {e}")

    def _hash_password(self, password: str) -> str:
        """Secure SHA-256 password hash."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    async def sign_up(self, req: SignUpRequest) -> Dict[str, Any]:
        """Registers a new user and returns user profile + session token."""
        clean_email = req.email.strip().lower()
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        password_hash = self._hash_password(req.password)
        token = f"sess_{uuid.uuid4().hex}"
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        user_data = {
            "id": user_id,
            "name": req.name.strip(),
            "email": clean_email,
            "role": req.role or "doctor",
            "email_verified": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if self.supabase_client:
            try:
                # 1. Insert user
                self.supabase_client.table("users").insert(user_data).execute()
                # 2. Insert account
                self.supabase_client.table("accounts").insert({
                    "id": f"acc_{uuid.uuid4().hex[:12]}",
                    "user_id": user_id,
                    "account_id": clean_email,
                    "provider_id": "credential",
                    "password": password_hash
                }).execute()
                # 3. Create session
                self.supabase_client.table("sessions").insert({
                    "id": f"sess_id_{uuid.uuid4().hex[:12]}",
                    "user_id": user_id,
                    "token": token,
                    "expires_at": expires_at
                }).execute()
                # 4. Generate default API Key
                default_key = f"sicce_{uuid.uuid4().hex[:20]}"
                self.supabase_client.table("api_keys").insert({
                    "id": f"key_{uuid.uuid4().hex[:12]}",
                    "user_id": user_id,
                    "key_value": default_key,
                    "name": "Default EMR Gateway Key",
                    "requests_count": 0,
                    "is_active": True
                }).execute()
            except Exception as e:
                logger.error(f"Supabase sign-up error: {e}. Falling back to local state.")
                self._save_local_user(user_data, password_hash, token, expires_at)
        else:
            self._save_local_user(user_data, password_hash, token, expires_at)

        return {
            "user": user_data,
            "session": {"token": token, "expires_at": expires_at}
        }

    def _save_local_user(self, user_data: Dict[str, Any], password_hash: str, token: str, expires_at: str):
        self._local_users[user_data["email"]] = user_data
        self._local_accounts[user_data["email"]] = password_hash
        self._local_sessions[token] = {
            "user": user_data,
            "token": token,
            "expires_at": expires_at
        }

    async def sign_in(self, req: SignInRequest) -> Dict[str, Any]:
        """Validates credentials and issues a fresh session token."""
        clean_email = req.email.strip().lower()
        password_hash = self._hash_password(req.password)
        token = f"sess_{uuid.uuid4().hex}"
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        user_record = None
        if self.supabase_client:
            try:
                acc_res = self.supabase_client.table("accounts").select("*").eq("account_id", clean_email).execute()
                if acc_res.data and acc_res.data[0]["password"] == password_hash:
                    usr_res = self.supabase_client.table("users").select("*").eq("id", acc_res.data[0]["user_id"]).execute()
                    if usr_res.data:
                        user_record = usr_res.data[0]
                        # Store new session
                        self.supabase_client.table("sessions").insert({
                            "id": f"sess_id_{uuid.uuid4().hex[:12]}",
                            "user_id": user_record["id"],
                            "token": token,
                            "expires_at": expires_at
                        }).execute()
            except Exception as e:
                logger.error(f"Supabase sign-in query failed: {e}")
                
        if not user_record:
            # Fallback to local user
            if self._local_accounts.get(clean_email) == password_hash:
                user_record = self._local_users.get(clean_email)
                self._local_sessions[token] = {
                    "user": user_record,
                    "token": token,
                    "expires_at": expires_at
                }

        if not user_record:
            raise ValueError("Invalid email or password")

        return {
            "user": user_record,
            "session": {"token": token, "expires_at": expires_at}
        }

    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Resolves user and session by session token."""
        if not token:
            return None
            
        if self.supabase_client:
            try:
                res = self.supabase_client.table("sessions").select("*, users(*)").eq("token", token).execute()
                if res.data and len(res.data) > 0:
                    sess = res.data[0]
                    return {
                        "user": sess.get("users"),
                        "session": {"token": sess["token"], "expires_at": sess["expires_at"]}
                    }
            except Exception as e:
                logger.error(f"Supabase get_session query failed: {e}")

        return self._local_sessions.get(token)

    async def create_api_key(self, user_id: str, name: str) -> Dict[str, Any]:
        """Creates a new B2B API Key for a clinic/doctor."""
        key_id = f"key_{uuid.uuid4().hex[:12]}"
        key_value = f"sicce_{uuid.uuid4().hex[:24]}"
        
        record = {
            "id": key_id,
            "user_id": user_id,
            "key_value": key_value,
            "name": name,
            "requests_count": 0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if self.supabase_client:
            try:
                self.supabase_client.table("api_keys").insert(record).execute()
            except Exception as e:
                logger.error(f"Supabase create_api_key failed: {e}")
                self._local_api_keys[key_value] = record
        else:
            self._local_api_keys[key_value] = record

        return record

    async def list_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """Lists all API keys belonging to a user."""
        if self.supabase_client:
            try:
                res = self.supabase_client.table("api_keys").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                return res.data or []
            except Exception as e:
                logger.error(f"Supabase list_api_keys failed: {e}")
                
        return [k for k in self._local_api_keys.values() if k.get("user_id") == user_id]

    async def validate_api_key(self, key_value: str) -> bool:
        """Validates an incoming X-API-KEY and increments its request counter."""
        if not key_value:
            return False
            
        # Check static dev keys
        static_keys = set(os.getenv("API_KEYS", "test-dev-key").split(","))
        if key_value in static_keys:
            return True

        if self.supabase_client:
            try:
                res = self.supabase_client.table("api_keys").select("*").eq("key_value", key_value).eq("is_active", True).execute()
                if res.data and len(res.data) > 0:
                    key_row = res.data[0]
                    # Increment request counter asynchronously
                    new_count = key_row.get("requests_count", 0) + 1
                    self.supabase_client.table("api_keys").update({
                        "requests_count": new_count,
                        "last_used_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", key_row["id"]).execute()
                    return True
            except Exception as e:
                logger.error(f"Supabase validate_api_key failed: {e}")

        # Check local fallback
        if key_value in self._local_api_keys and self._local_api_keys[key_value].get("is_active"):
            self._local_api_keys[key_value]["requests_count"] += 1
            return True

        return False
