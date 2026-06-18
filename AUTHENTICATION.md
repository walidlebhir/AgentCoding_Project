# SpringForge CLI Authentication System

## Overview

The SpringForge CLI now includes a complete token-based authentication system that allows users to securely authenticate with the FastAPI backend server. This enables:

- User registration and account creation
- Secure login with email and password
- Automatic token storage and management
- Token-based authorization for all API requests
- Multi-user support with user switching

## Architecture

### Components

#### 1. **token_storage.py** - Secure Token Storage
- Stores authentication tokens locally in `~/.springforge/auth.json`
- File permissions: `600` (read/write for owner only)
- Supports multiple user accounts
- Atomic file operations for data integrity
- Methods:
  - `save_token(email, token)` - Store user token
  - `get_token(email)` - Retrieve user token
  - `get_current_user()` - Get logged-in user
  - `remove_token(email)` - Logout user
  - `list_users()` - List all stored users

#### 2. **auth_manager.py** - Authentication Logic
- Handles registration, login, and logout operations
- Communicates with FastAPI backend at `/api/register` and `/api/login`
- Manages token lifecycle
- Methods:
  - `register(name, email, password)` - Create new account
  - `login(email, password)` - Authenticate user
  - `logout(email)` - Remove user token
  - `is_authenticated()` - Check if user is logged in
  - `get_current_user()` - Get current user email

#### 3. **Enhanced ApiClient** - Automatic Authorization
- Automatically includes Bearer token in all API requests
- Token retrieved from local storage
- Transparent token injection in request headers
- Headers format: `Authorization: Bearer <jwt_token>`

#### 4. **CLI Commands** - User Interface
Added new CLI commands for authentication management.

## Usage

### Interactive Mode

```bash
# Start interactive CLI
springforge

# Within the CLI, use authentication commands:
/login       # Interactive login prompt
/register    # Interactive registration
/logout      # Logout current user
/user        # Show current user
/users       # List all users
/help        # Show all commands
```

### Command Line Mode

```bash
# Register new user
springforge register

# Login to account
springforge login

# Logout
springforge logout

# Check current user
springforge user

# List users
springforge users
```

## Authentication Flow

### Registration Flow

```
1. User runs: springforge register
2. Prompted for: name, email, password
3. CLI sends: POST /api/register
   {
     "name": "John Doe",
     "email": "john@example.com",
     "password": "secure_password"
   }
4. Server validates and creates user
5. CLI automatically logs user in
6. Token stored in ~/.springforge/auth.json
```

### Login Flow

```
1. User runs: springforge login
2. Prompted for: email, password
3. CLI sends: POST /api/login
   {
     "email": "john@example.com",
     "password": "secure_password"
   }
4. Server validates credentials
5. Server returns: {"access_token": "<jwt>", "token_type": "bearer"}
6. CLI stores token in local storage
7. Token automatically included in all future requests
```

### API Request with Token

```
All API requests now include Authorization header:

POST /generate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "prompt": "Create a user management system"
}
```

## Token Storage Format

Tokens are stored in `~/.springforge/auth.json`:

```json
{
  "current_user": "john@example.com",
  "users": {
    "john@example.com": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    },
    "jane@example.com": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
  }
}
```

## Security Considerations

1. **File Permissions**: Token file has `600` permissions (owner read/write only)
2. **Token Location**: Stored in user home directory, not in version control
3. **Token in Requests**: Included in Authorization header, not in URL or body
4. **No Token Logging**: Token values are masked in logs
5. **Atomic Operations**: File writes are atomic to prevent corruption
6. **Local Storage Only**: Tokens stored only locally, not transmitted unnecessarily

## Server-Side Integration

### FastAPI Requirements

The FastAPI backend must have:

1. **Authentication Routes**:
   - `POST /api/register` - User registration
   - `POST /api/login` - User authentication

2. **JWT Token Generation**:
   - Using `PyJWT` library
   - Token contains: `user_id`, `role`, `exp` (expiration)
   - Algorithm: HS256

3. **Authorization Dependency**:
   - `get_current_user()` dependency
   - Extracts user from Bearer token
   - Validates token expiration and signature

4. **Protected Endpoints**:
   - All endpoints that require authentication
   - Use `Depends(get_current_user)` decorator
   - Example: `POST /generate` requires authentication

## Configuration

### Environment Variables

Set the API URL in your environment:

```bash
export SPRINGFORGE_API_URL=http://localhost:8000
```

Default: `http://localhost:8000`

### Token Expiration

Token expiration is controlled by the FastAPI server:

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # In src/core/config.py
```

## Multi-User Support

The CLI supports multiple user accounts on the same machine:

```bash
# Login as first user
/login
# Email: alice@example.com
# Password: ****

# Later, switch to another user
/logout
/login
# Email: bob@example.com
# Password: ****

# View all stored users
/users
# Output:
# Stored users (2):
#   - alice@example.com *
#   - bob@example.com
```

## Troubleshooting

### "No user logged in" Error

```bash
# Solution: Login first
/login
```

### "Invalid email or password" Error

```bash
# Verify credentials are correct
# Try registering a new account if needed
/register
```

### Token Expired

Tokens expire after 30 minutes. Simply login again:

```bash
/login
```

### Clear All Stored Tokens

```bash
# Delete the auth file manually
rm ~/.springforge/auth.json
```

## Examples

### Example 1: Complete Workflow

```bash
# Start CLI
springforge

# Register new user
/register
# Full Name: John Developer
# Email: john@example.com
# Password: MySecurePassword123
# Confirm Password: MySecurePassword123

# Now automatically logged in, generate a project
generate "REST API with user management"

# Check current user
/user
# Output: Current user: john@example.com

# Logout
/logout
```

### Example 2: Command Line Generation

```bash
# Login
springforge login
# Email: john@example.com
# Password: ****

# Generate project from command line
springforge generate "Spring Boot REST API"

# Logout
springforge logout
```

## API Response Examples

### Successful Registration

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "USER"
}
```

### Successful Login

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJyb2xlIjoiVVNFUiIsImV4cCI6MTY3ODkwMTIzNH0.signature",
  "token_type": "bearer"
}
```

### Project Generation (Authenticated)

```json
{
  "success": true,
  "project_id": "proj_20260617_181403_4907",
  "db_id": "12345",
  "message": "Projet genere avec succes",
  "download_url": "http://localhost:8000/download/proj_20260617_181403_4907",
  "filename": "proj_20260617_181403_4907.zip",
  "request_id": "a1b2c3d4",
  "duration_seconds": 45.3,
  "llm_calls": 5,
  "files_generated": 42,
  "provider": "gemini-2.5-flash"
}
```

## Future Enhancements

Potential improvements to the authentication system:

1. **Token Refresh**: Implement refresh tokens for longer sessions
2. **Password Reset**: Add email-based password reset flow
3. **2FA**: Two-factor authentication support
4. **Session Management**: Track active sessions
5. **Token Revocation**: Server-side token blacklisting
6. **API Keys**: Support for programmatic access with API keys

## Support

For authentication issues, check:

1. Network connectivity to FastAPI server
2. User email and password are correct
3. Token file permissions: `ls -la ~/.springforge/auth.json`
4. API server is running: `springforge health`
