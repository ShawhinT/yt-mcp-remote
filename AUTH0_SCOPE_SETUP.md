# Auth0 API Scope Configuration (Deprecated for this server)

This server now accepts tokens based on issuer and audience only. You do not need to configure an `mcp:access` scope/permission.

## Current Behavior

The MCP server validates only:

1. Issuer: your Auth0 tenant domain
2. Audience: `https://yt-mcp-remote-production.up.railway.app`

`scope`/`permissions` claims are optional and used only for logging.

## Auth0 Dashboard Configuration

### Step 1: Navigate to Your API

1. Log in to [Auth0 Dashboard](https://manage.auth0.com/)
2. Go to **Applications** → **APIs**
3. Find and click on your API:
   - **Identifier**: `https://yt-mcp-remote-production.up.railway.app`

### Step 2: (Optional) Permissions

You may skip adding `mcp:access`. If you later reintroduce granular permissions, add them here and update the server accordingly.

### Step 3: Verify Configuration

After adding the permission, you should see:

```
Permission (Scope)  | Description
--------------------|----------------------------------
mcp:access          | Access MCP server tools and resources
```

### Step 4: API Settings Checklist

While you're in the API settings, verify these configurations:

**Settings Tab**:
- ✅ **Identifier**: `https://yt-mcp-remote-production.up.railway.app`
- ✅ **Signing Algorithm**: RS256
- ✅ **RBAC Settings** (optional but recommended):
  - Enable RBAC: ON
  - Add Permissions in the Access Token: ON
- ✅ **Allow Offline Access**: ON (if you want refresh tokens)

**Permissions Tab**:
- ✅ `mcp:access` permission exists

### Step 5: Default Directory (Optional)

If you want to auto-assign this permission to users:

1. Go to **User Management** → **Roles**
2. Create a role (e.g., "MCP User")
3. Add `mcp:access` permission to the role
4. Assign users to this role

Alternatively, permissions can be granted during the OAuth consent screen.

## What Happens During OAuth Flow

### Before (Without Scope)

```
ChatGPT → Auth0: GET /authorize?scope=openid profile email
Auth0 → Issues token with audience: /userinfo
MCP Server → Rejects token (wrong audience)
```

### After (With Scope)

```
ChatGPT → Auth0: GET /authorize?scope=openid profile email mcp:access
Auth0 → Detects API scope request
Auth0 → Issues token with audience: https://yt-mcp-remote-production.up.railway.app
Auth0 → Includes mcp:access in token permissions
MCP Server → Validates audience ✅
MCP Server → Validates scope ✅
MCP Server → Grants access ✅
```

## User Consent Screen

When a user authorizes ChatGPT to access the MCP server, they'll see a consent screen like:

```
ChatGPT is requesting permission to:

✓ Access your profile information (openid, profile, email)
✓ Access MCP server tools and resources (mcp:access)

[Authorize] [Deny]
```

## Verifying the Setup

### Test 1: Check Protected Resource Metadata

```bash
curl -s http://localhost:8000/.well-known/oauth-protected-resource
```

Should return (note: `scopes_supported` may be empty or omitted):
```json
{
  "resource": "https://yt-mcp-remote-production.up.railway.app/",
  "authorization_servers": ["https://dev-x1k2ea1lh5dffa3a.us.auth0.com/"],
  "scopes_supported": [],
  "bearer_methods_supported": ["header"]
}
```
Note: `scopes_supported` may be omitted entirely.

### Test 2: Manual OAuth Flow

1. Construct authorization URL:
```
https://dev-x1k2ea1lh5dffa3a.us.auth0.com/authorize?
  response_type=code
  &client_id=<YOUR_CLIENT_ID>
  &redirect_uri=<YOUR_REDIRECT_URI>
  &scope=openid profile email
  &audience=https://yt-mcp-remote-production.up.railway.app
```

2. Complete the flow and exchange code for token

3. Decode the JWT token (use jwt.io):
   - Check `aud` claim: Should be `https://yt-mcp-remote-production.up.railway.app`
   - `scope`/`permissions` claims are optional

### Test 3: Monitor Auth0 Logs

Go to **Monitoring** → **Logs** in Auth0 Dashboard.

Look for successful token exchange events (`seacft`) with:
```json
{
  "grantInfo": {
    "audience": "https://yt-mcp-remote-production.up.railway.app",
    "scope": "openid profile email mcp:access"
  }
}
```

**Before fix**: `audience` was `/userinfo`
**After fix**: `audience` should be your API URL

## Troubleshooting

### Issue: Permission not showing in consent screen

**Solution**:
- Ensure "Add Permissions in the Access Token" is enabled in API settings
- Clear browser cache or use incognito mode
- Check that the permission is spelled exactly `mcp:access`

### Issue: Token still has wrong audience

**Solution**:
- Ensure the API identifier exactly matches your environment variable
- If the client cannot pass `audience`, set Default Audience to your API identifier

### Issue: "Insufficient scope" error

**Solution**:
- Scopes are not required with this server configuration. Ensure the server changes are deployed.

### Issue: Permission not appearing in token

**Solution**:
- Not required for this server configuration.

## Additional Scopes (Future Enhancement)

You can add more granular permissions:

```
mcp:read:transcripts   - Read video transcripts
mcp:write:chapters     - Generate video chapters
mcp:admin              - Administrative access
```

If you reintroduce scopes later:
1. Add Auth0 API Permissions
2. Re-add `required_scopes` in `main.py`
3. Reinstate scope validation in `utils/auth.py`

## References

- [Auth0 API Permissions](https://auth0.com/docs/get-started/apis/api-settings#permissions)
- [Auth0 RBAC](https://auth0.com/docs/manage-users/access-control/rbac)
- [OAuth 2.0 Scopes](https://datatracker.ietf.org/doc/html/rfc6749#section-3.3)
