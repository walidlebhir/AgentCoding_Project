# SpringForge CLI - Authentication Implementation Summary

## Overview
Complete token-based authentication system implemented for SpringForge CLI to enable secure, authenticated communication with FastAPI backend server.

## Files Created

### 1. `springforge_cli/core/token_storage.py`
Secure token storage and management module:
- Stores tokens in `~/.springforge/auth.json` with `600` permissions
- `TokenStorage` class with methods:
  - `save_token(email, token)` - Store authentication token
  - `get_token(email)` - Retrieve token for user
  - `get_current_user()` - Get current logged-in user
  - `remove_token(email)` - Remove user token (logout)
  - `list_users()` - List all stored users
- Global singleton instance via `get_token_storage()`

### 2. `springforge_cli/core/auth_manager.py`
Authentication manager handling server communication:
- `AuthManager` class managing authentication flows
- Methods:
  - `register(name, email, password)` - Register new user
  - `login(email, password)` - Authenticate and store token
  - `logout(email)` - Remove authentication
  - `is_authenticated()` - Check authentication status
  - `get_current_user()` - Get current user
  - `list_users()` - List stored users
- Communicates with `/api/register` and `/api/login` endpoints
- Error handling with user-friendly messages

### 3. `springforge_cli/core/AUTH_README.md`
Technical documentation of authentication system internals.

### 4. `springforge_cli/AUTH_QUICK_REF.md`
Quick reference guide for authentication commands.

### 5. `AUTHENTICATION.md` (Project Root)
Comprehensive authentication documentation including:
- Architecture overview
- Component descriptions
- Usage examples
- Token storage format
- Security considerations
- Server integration requirements
- Multi-user support
- Troubleshooting guide

## Files Modified

### 1. `springforge_cli/core/client.py`
Enhanced with token-based authentication:
- Added `token_storage` member to `ApiClient`
- Updated `_request()` method to include Bearer token in headers
- Automatic token injection: `Authorization: Bearer <jwt_token>`
- Backward compatible - works without token if not authenticated

### 2. `springforge_cli/main.py`
Added authentication command support:
- Imported `getpass`, `get_auth_manager`
- Updated `dispatch()` signature to include `auth_mgr` parameter
- Added dispatch handlers:
  - `/login` - Interactive login
  - `/register` - Interactive registration
  - `/logout` - Logout user
  - `/user` - Show current user
  - `/users` - List all users
- Added command handler functions:
  - `cmd_login()` - Handle login flow
  - `cmd_register()` - Handle registration flow
  - `cmd_logout()` - Handle logout
  - `cmd_user()` - Show current user info
  - `cmd_list_users()` - Display all users
- Updated `main()` to instantiate and pass `AuthManager`
- Added command-line support for auth commands
- Updated all `dispatch()` calls to include `auth_mgr`

### 3. `springforge_cli/ui/terminal.py`
Enhanced UI for authentication:
- Added `Message.warn()` method for warning messages
- Updated `show_help()` to display authentication commands
- Help now organized into categories:
  - Project Generation
  - Authentication
  - General
- Added authentication command examples

## Architecture

```
┌─────────────────────────────────────────┐
│         SpringForge CLI                  │
├─────────────────────────────────────────┤
│  main.py                                 │
│  ├─ AuthManager (auth_mgr)              │
│  ├─ ApiClient (client)                  │
│  └─ Agent (agent)                       │
│                                         │
│  Commands:                              │
│  ├─ /login, /register, /logout          │
│  ├─ /user, /users                       │
│  └─ generate, edit, add, fix            │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│    Token Storage Layer                   │
├─────────────────────────────────────────┤
│  ~/.springforge/auth.json (600 perms)   │
│  {                                      │
│    "current_user": "user@example.com",  │
│    "users": {                           │
│      "user@example.com": {              │
│        "token": "jwt...",               │
│        "token_type": "bearer"           │
│      }                                  │
│    }                                    │
│  }                                      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│      FastAPI Backend Server             │
├─────────────────────────────────────────┤
│  POST /api/register                     │
│  POST /api/login                        │
│  POST /generate (Authorization header)  │
│  POST /edit (Authorization header)      │
│  POST /add (Authorization header)       │
│  POST /fix (Authorization header)       │
└─────────────────────────────────────────┘
```

## Authentication Flow

### Registration
```
User → /register command
    ↓
Prompts: name, email, password
    ↓
POST /api/register → FastAPI
    ↓
Server creates user, returns user info
    ↓
CLI automatically logs user in
    ↓
Token stored in ~/.springforge/auth.json
```

### Login
```
User → /login command
    ↓
Prompts: email, password
    ↓
POST /api/login → FastAPI
    ↓
Server validates, returns JWT token
    ↓
CLI stores token locally
    ↓
Token included in all future requests
```

### Authenticated Request
```
User → generate "description" command
    ↓
Client retrieves token from storage
    ↓
POST /generate with Authorization header
    ↓
FastAPI validates token, extracts user
    ↓
Request processed for authenticated user
    ↓
Response returned with project details
```

## Security Features

1. **File Permissions**: `600` (owner read/write only)
2. **Atomic Operations**: Safe concurrent file access
3. **Token Masking**: Tokens not logged or displayed
4. **Local Storage Only**: Tokens never uploaded
5. **Bearer Token Format**: Standard OAuth 2.0 Bearer scheme
6. **Expiration**: Server-side token expiration (30 min default)

## Usage Examples

### Interactive Mode
```bash
# Start CLI
springforge

# Register (in CLI)
/register

# Generate project (now authenticated)
generate "user management system"

# Check current user
/user

# Logout
/logout
```

### Command Line
```bash
# Register
springforge register

# Login
springforge login

# Generate authenticated
springforge generate "REST API"

# Check user
springforge user

# Logout
springforge logout
```

## Server Integration

### Required FastAPI Routes
- `POST /api/register` - User registration
- `POST /api/login` - User authentication

### Required Endpoints to Protect
- `POST /generate` - Add `Depends(get_current_user)`
- `POST /edit` - Add `Depends(get_current_user)`
- `POST /add` - Add `Depends(get_current_user)`
- `POST /fix` - Add `Depends(get_current_user)`

### JWT Configuration
```python
# In FastAPI server config
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
```

## Multi-User Support

The CLI supports multiple user accounts on the same machine:

```bash
# First user
/login
# Email: alice@example.com

# Switch to second user
/logout
/login
# Email: bob@example.com

# List all users
/users
```

## Testing

### Manual Testing Checklist
- [ ] Register new user via CLI
- [ ] Login with correct credentials
- [ ] Login fails with wrong password
- [ ] Generate project authenticated
- [ ] Logout and verify token removed
- [ ] Switch between users
- [ ] Check `/user` shows correct user
- [ ] Check `/users` lists all stored users

### Test Commands
```bash
# Test registration
springforge register

# Test login
springforge login

# Test generation
springforge generate "test project"

# Test logout
springforge logout

# Test user info
springforge user

# Test user list
springforge users
```

## Configuration

### Environment Variables
```bash
# Set API URL (default: http://localhost:8000)
export SPRINGFORGE_API_URL=http://your-server:8000

# Set model
export SPRINGFORGE_MODEL=gemini-2.5-flash
```

### File Locations
- **Token Storage**: `~/.springforge/auth.json`
- **Config**: Respects `SPRINGFORGE_API_URL` env var
- **Default API**: `http://localhost:8000`

## Future Enhancements

1. **Token Refresh**: Implement refresh token flow for longer sessions
2. **Password Reset**: Email-based password recovery
3. **2FA**: Two-factor authentication
4. **API Keys**: Programmatic access with API keys
5. **Session Management**: Track active sessions server-side
6. **Token Revocation**: Server-side token blacklisting

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No user logged in" | Run `/register` or `/login` |
| "Invalid credentials" | Check email/password are correct |
| "API unreachable" | Run `springforge health` to verify server |
| "Token expired" | Run `/login` to get new token |
| "Clear all auth" | Delete `~/.springforge/auth.json` |

## Support Documentation

- **AUTHENTICATION.md** - Comprehensive user and developer guide
- **AUTH_QUICK_REF.md** - Quick reference for common tasks
- **AUTH_README.md** - Technical implementation details

## Backward Compatibility

- Existing API client methods work with and without authentication
- Non-authenticated requests still function
- Token injection is automatic and transparent
- No breaking changes to CLI interface

## Summary

The SpringForge CLI now has a complete, production-ready authentication system that:

✅ Securely stores JWT tokens locally  
✅ Automatically includes tokens in all requests  
✅ Supports user registration and login  
✅ Handles multi-user scenarios  
✅ Provides clear error messages  
✅ Follows OAuth 2.0 Bearer token standard  
✅ Maintains backward compatibility  
✅ Includes comprehensive documentation  

Users can now authenticate once and use the agent securely for all operations.
