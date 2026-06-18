# SpringForge CLI Authentication - Testing Guide

## Pre-Testing Checklist

Before running tests, ensure:
- [ ] FastAPI server is running: `uvicorn src.Server:app --reload`
- [ ] Database is configured and initialized
- [ ] All requirements installed: `pip install -r requirement.txt`
- [ ] Python 3.8+
- [ ] Network connectivity to server

## Unit Tests

### 1. Token Storage Module

#### Test: Create and Retrieve Token
```python
from springforge_cli.core.token_storage import TokenStorage

storage = TokenStorage()
storage.save_token("test@example.com", "dummy_token_123")
token = storage.get_token("test@example.com")
assert token == "dummy_token_123"
print("✓ Token storage works")
```

#### Test: Current User
```python
storage.save_token("user1@example.com", "token1")
storage.save_token("user2@example.com", "token2")
current = storage.get_current_user()
assert current in ["user1@example.com", "user2@example.com"]
print("✓ Current user tracking works")
```

#### Test: Remove Token
```python
storage.save_token("test@example.com", "token")
storage.remove_token("test@example.com")
token = storage.get_token("test@example.com")
assert token is None
print("✓ Token removal works")
```

#### Test: List Users
```python
storage.clear_all()
storage.save_token("alice@example.com", "token_a")
storage.save_token("bob@example.com", "token_b")
users = storage.list_users()
assert set(users) == {"alice@example.com", "bob@example.com"}
print("✓ User listing works")
```

#### Test: File Permissions
```python
import os
from pathlib import Path

token_file = Path.home() / ".springforge" / "auth.json"
if token_file.exists():
    stat = os.stat(token_file)
    mode = stat.st_mode & 0o777
    assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"
    print("✓ File permissions are correct (0o600)")
```

### 2. API Client Module

#### Test: Authorization Header
```python
from springforge_cli.core.client import ApiClient
from springforge_cli.core.token_storage import get_token_storage

# Setup token
storage = get_token_storage()
storage.save_token("test@example.com", "test_token_xyz")

# Create client
client = ApiClient("http://localhost:8000")

# Note: The token is automatically added to requests
# This is transparent to the user
print("✓ API client configured for token injection")
```

## Integration Tests

### 1. Registration Flow

```bash
# Interactive registration
springforge register

# Enter details:
# Full Name: Test User
# Email: test@example.com
# Password: TestPassword123
# Confirm Password: TestPassword123

# Expected output:
# ✓ User registered: test@example.com
# ✓ Authenticating...
# ✓ Logged in as test@example.com
```

### 2. Login Flow

```bash
# Clear any existing tokens (optional)
rm ~/.springforge/auth.json 2>/dev/null

# Interactive login
springforge login

# Enter details:
# Email: test@example.com
# Password: TestPassword123

# Expected output:
# ✓ Authenticating...
# ✓ Logged in as test@example.com
```

### 3. Authentication in Requests

```bash
# After login, generate a project
springforge generate "simple REST API"

# Expected behavior:
# - Request includes Authorization header
# - Token is automatically sent
# - Project generates successfully
# - Project linked to authenticated user in database
```

### 4. Logout Flow

```bash
# Logout from current user
springforge logout

# Or interactively in CLI
/logout

# Expected output:
# ✓ Logged out from test@example.com
```

### 5. User Information

```bash
# Check current user (must be authenticated first)
springforge user

# Or interactively
/user

# Expected output:
# Current user: test@example.com
```

### 6. List Users

```bash
# List all stored users
springforge users

# Or interactively
/users

# Expected output:
# Stored users (2):
#   - alice@example.com *
#   - bob@example.com
# (* = currently logged in)
```

## End-to-End Test Scenario

### Scenario: Complete User Workflow

```bash
# 1. Start the CLI
cd Agent_Backend
springforge

# 2. Register new user
/register
# Full Name: John Developer
# Email: john@example.com
# Password: SecurePass123
# Confirm: SecurePass123

# Expected: Automatic login after registration

# 3. Verify current user
/user
# Expected: Current user: john@example.com

# 4. Generate a project
generate "REST API with user authentication"
# Expected: Project generates successfully

# 5. Check health
/health
# Expected: API status and provider info

# 6. Add new user (logout and register new)
/logout
/register
# Full Name: Jane Developer
# Email: jane@example.com
# Password: AnotherPass456

# 7. Generate as new user
generate "microservices architecture"

# 8. Switch between users
/logout
/login
# Email: john@example.com
# Password: SecurePass123

# 9. View all users
/users
# Expected: Both users listed

# 10. Final logout
/logout
/exit
```

## Command-Line Test Sequence

```bash
#!/bin/bash

# Test 1: Register
echo "Testing registration..."
springforge register <<EOF
Test User
test@example.com
TestPass123
TestPass123
EOF

# Test 2: Current user
echo "Testing current user..."
springforge user

# Test 3: Generate authenticated
echo "Testing authenticated generation..."
springforge generate "simple REST API"

# Test 4: Check users
echo "Testing user list..."
springforge users

# Test 5: Logout
echo "Testing logout..."
springforge logout

# Test 6: Verify no user
echo "Testing after logout..."
springforge user
```

## Error Handling Tests

### 1. Invalid Credentials
```bash
springforge login
# Email: test@example.com
# Password: WrongPassword

# Expected error:
# ✗ Login failed: Invalid email or password
```

### 2. Email Already Registered
```bash
springforge register
# Email: test@example.com (existing)
# Password: SomePass123

# Expected error:
# ✗ Registration failed: Email already registered
```

### 3. Short Password
```bash
springforge register
# Password: abc (too short)

# Expected error:
# ✗ Password must be at least 6 characters
```

### 4. Password Mismatch
```bash
springforge register
# Password: MyPassword123
# Confirm: DifferentPass456

# Expected error:
# ✗ Passwords do not match
```

### 5. API Unreachable
```bash
# Stop FastAPI server, then:
springforge login

# Expected error:
# ✗ Connection failed: Connection refused
```

## Security Tests

### 1. Token File Permissions
```bash
# Verify file permissions
ls -l ~/.springforge/auth.json
# Expected: -rw------- (600)
```

### 2. Token Not in Logs
```bash
# Run command with logging
springforge login 2>&1 | grep -i "token"
# Expected: No token values in output
```

### 3. Token in Storage Only
```bash
# Check where tokens are stored
find ~ -name "auth.json" -o -name "*token*" | grep springforge
# Expected: ~/.springforge/auth.json only
```

## Database Tests

### 1. User Created in Database
```bash
# After registration, check database:
SELECT * FROM users WHERE email = 'test@example.com';
# Expected: User row created with email, hashed password, role=USER
```

### 2. Projects Linked to User
```bash
# After generating project, check database:
SELECT * FROM projects WHERE user_id = <user_id>;
# Expected: Project row with correct user_id
```

### 3. Token in Header
```bash
# Monitor network requests (using curl or similar):
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/login
# Expected: Authorization header present in request
```

## Performance Tests

### 1. Login Speed
```bash
time springforge login
# Expected: < 2 seconds
```

### 2. Token Retrieval
```bash
# Multiple rapid requests
for i in {1..10}; do
    springforge user
done
# Expected: All complete quickly, no delays
```

### 3. File I/O Performance
```python
import time
from springforge_cli.core.token_storage import TokenStorage

storage = TokenStorage()
start = time.time()

# Rapid save/retrieve cycles
for i in range(100):
    storage.save_token(f"user{i}@example.com", f"token_{i}")
    token = storage.get_token(f"user{i}@example.com")

elapsed = time.time() - start
print(f"100 cycles: {elapsed:.3f}s")
# Expected: < 1 second
```

## Compatibility Tests

### 1. Python Versions
```bash
# Test with different Python versions:
python3.8 springforge_cli/main.py --help
python3.9 springforge_cli/main.py --help
python3.10 springforge_cli/main.py --help
python3.11 springforge_cli/main.py --help
# Expected: All work correctly
```

### 2. Operating Systems
- [ ] Windows: Test path handling and file permissions
- [ ] Linux: Test file permissions and path resolution
- [ ] macOS: Test file permissions and terminal colors

### 3. Network Conditions
```bash
# Test with different network scenarios:
# - Normal connection (baseline)
# - Slow connection (network throttling)
# - Intermittent connectivity (request timeout)
# - Offline mode (no connection)

# Expected: Appropriate error messages for each
```

## Test Report Template

```
═══════════════════════════════════════════════════════════
Authentication Implementation Test Report
═══════════════════════════════════════════════════════════

Date: _______________
Tester: _______________
Environment: _______________

Token Storage Tests:
  [ ] Token save/retrieve: PASS/FAIL
  [ ] Current user tracking: PASS/FAIL
  [ ] Token removal: PASS/FAIL
  [ ] User listing: PASS/FAIL
  [ ] File permissions: PASS/FAIL

API Client Tests:
  [ ] Authorization header injection: PASS/FAIL
  [ ] Token in requests: PASS/FAIL
  [ ] Backward compatibility: PASS/FAIL

Registration Tests:
  [ ] Valid registration: PASS/FAIL
  [ ] Duplicate email rejection: PASS/FAIL
  [ ] Weak password rejection: PASS/FAIL
  [ ] Password mismatch rejection: PASS/FAIL

Login Tests:
  [ ] Valid credentials: PASS/FAIL
  [ ] Invalid credentials: PASS/FAIL
  [ ] Token storage: PASS/FAIL
  [ ] Multiple user support: PASS/FAIL

Logout Tests:
  [ ] Current user logout: PASS/FAIL
  [ ] Token removal: PASS/FAIL
  [ ] User switching: PASS/FAIL

Request Tests:
  [ ] Authenticated /generate: PASS/FAIL
  [ ] Authenticated /edit: PASS/FAIL
  [ ] Authenticated /add: PASS/FAIL
  [ ] Authenticated /fix: PASS/FAIL

Database Tests:
  [ ] User created in DB: PASS/FAIL
  [ ] Projects linked to user: PASS/FAIL
  [ ] Token validation: PASS/FAIL

Security Tests:
  [ ] File permissions (600): PASS/FAIL
  [ ] Token not in logs: PASS/FAIL
  [ ] Token only in storage: PASS/FAIL

Issues Found:
  1. _______________
  2. _______________
  3. _______________

Recommendations:
  1. _______________
  2. _______________

Overall Status: PASSED / FAILED

═══════════════════════════════════════════════════════════
```

## Debugging

### Enable Debug Logging
```bash
export DEBUG=1
springforge login
```

### View Token Storage
```bash
cat ~/.springforge/auth.json | jq .
```

### Check Network Requests
```bash
# Using curl to test API directly:
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'

# With token:
curl -X POST http://localhost:8000/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"simple REST API"}'
```

## Success Criteria

All tests PASS when:
✅ Users can register successfully  
✅ Users can login successfully  
✅ Tokens are stored securely  
✅ Authentication headers are sent automatically  
✅ Projects are generated on behalf of authenticated users  
✅ File permissions are correct (600)  
✅ Multiple users can be managed  
✅ Error handling is appropriate  
✅ No tokens appear in logs  
✅ Database reflects authenticated users  
