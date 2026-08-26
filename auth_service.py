import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    logger.warning("argon2-cffi not installed, falling back to secure hashing.")

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
    """Manages user registration, session tokens, and dynamic B2B API keys using Argon2id & Supabase."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_client = None
        self.ph = PasswordHasher() if ARGON2_AVAILABLE else None
        
        # Local fallback in-memory stores if Supabase is offline/mocked
        self._local_users: Dict[str, Dict[str, Any]] = {}
        self._local_accounts: Dict[str, str] = {} # email -> hashed password
        self._local_sessions: Dict[str, Dict[str, Any]] = {} # token -> session data
        self._local_api_keys: Dict[str, Dict[str, Any]] = {}
        # Seed the local fallback store ONLY from explicit env config (never hardcoded).
        _env_keys = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]
        if _env_keys:
            for i, k in enumerate(_env_keys):
                self._local_api_keys[k] = {"user_id": f"usr_env_{i}", "name": f"Env Key #{i+1}", "is_active": True, "requests_count": 0}
        
        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
                logger.info("AuthService connected to Supabase PostgreSQL.")
            except Exception as e:
                logger.error(f"AuthService failed to init Supabase client: {e}")

    def _hash_password(self, password: str) -> str:
        """Secure Argon2id password hash (per MASTER_DIRECTIVE.md Law #8)."""
        if self.ph:
            return self.ph.hash(password)
        # Fallback only if argon2 is not loaded
        salt = uuid.uuid4().hex
        return f"sha256${salt}${hashlib.sha256((salt + password).encode('utf-8')).hexdigest()}"

    def _verify_password(self, password: str, stored_hash: str) -> tuple[bool, Optional[str]]:
        """
        Verifies password against stored hash.
        Supports transparent migration from legacy SHA-256 to Argon2id.
        Returns (is_valid, new_hash_to_save_if_migrated).
        """
        if not stored_hash:
            return False, None

        # 1. Argon2id Hash Check
        if stored_hash.startswith("$argon2"):
            if self.ph:
                try:
                    self.ph.verify(stored_hash, password)
                    # Check if hash needs rehash due to parameter change
                    if self.ph.check_needs_rehash(stored_hash):
                        return True, self._hash_password(password)
                    return True, None
                except VerifyMismatchError:
                    return False, None
                except Exception as e:
                    logger.error(f"Argon2 verification error: {e}")
                    return False, None

        # 2. Legacy Plain SHA-256 (64 hex characters) migration
        if len(stored_hash) == 64 and all(c in "0123456789abcdefABCDEF" for c in stored_hash):
            candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
            if candidate.lower() == stored_hash.lower():
                logger.info("Migrating legacy SHA-256 hash to Argon2id.")
                new_hash = self._hash_password(password)
                return True, new_hash
            return False, None

        # 3. Salted SHA-256 fallback
        if stored_hash.startswith("sha256$"):
            parts = stored_hash.split("$")
            if len(parts) == 3:
                salt, expected = parts[1], parts[2]
                candidate = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
                if candidate == expected:
                    new_hash = self._hash_password(password)
                    return True, new_hash

        return False, None

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
                    "name": "Default API Key",
                    "is_active": True
                }).execute()
            except Exception as e:
                logger.error(f"Supabase user insert failed: {e}. Falling back to local store.")
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
        """Validates credentials via Argon2id and issues a fresh session token."""
        clean_email = req.email.strip().lower()
        token = f"sess_{uuid.uuid4().hex}"
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        user_record = None
        if self.supabase_client:
            try:
                acc_res = self.supabase_client.table("accounts").select("*").eq("account_id", clean_email).execute()
                if acc_res.data:
                    account = acc_res.data[0]
                    stored_hash = account["password"]
                    is_valid, new_hash = self._verify_password(req.password, stored_hash)
                    
                    if is_valid:
                        usr_res = self.supabase_client.table("users").select("*").eq("id", account["user_id"]).execute()
                        if usr_res.data:
                            user_record = usr_res.data[0]
                            # Migrate hash in DB if needed
                            if new_hash:
                                self.supabase_client.table("accounts").update({"password": new_hash}).eq("id", account["id"]).execute()
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
            stored_local_hash = self._local_accounts.get(clean_email)
            if stored_local_hash:
                is_valid, new_hash = self._verify_password(req.password, stored_local_hash)
                if is_valid:
                    user_record = self._local_users.get(clean_email)
                    if new_hash:
                        self._local_accounts[clean_email] = new_hash
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
            
        # Static keys come ONLY from the API_KEYS env var (comma-separated).
        # No baked-in defaults: an unconfigured deployment accepts no static keys.
        raw_keys = os.getenv("API_KEYS", "")
        static_keys = {k.strip() for k in raw_keys.split(",") if k.strip()}
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
