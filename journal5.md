# journal #5: kingdom technical deep dive

## january 15, 2026

spent most of today actually building kingdom. less theory, more code. documenting the technical decisions and implementation details while they're fresh.

---

## architecture overview

### the stack

went with a pretty standard modern stack:
- **frontend**: react + typescript. no framework overkill, just vite for bundling
- **backend**: node.js with express. considered fastify but express has better ecosystem support for what we need
- **database**: postgresql. needed relational data with good query performance
- **auth**: jwt tokens with refresh rotation. no third-party auth provider—wanted full control
- **hosting**: planning for vercel (frontend) + railway (backend + db)

### why these choices

**react + typescript** because:
- typescript catches bugs before they hit production
- react's component model maps well to kingdom's ui structure
- huge ecosystem means less reinventing wheels
- team already knows it

**postgresql over mongodb** because:
- our data is inherently relational. users have resources, resources have categories, categories have permissions
- joins are cleaner than document lookups
- transactions matter when we're dealing with resource allocation
- postgres has gotten really good at json if we need flexibility

**no orms**. writing raw sql with a query builder (using pg-promise). orms hide too much and make debugging painful. plus the sql isn't that complex.

---

## data model

### core entities

```sql
-- users table
create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  display_name text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- resources - the main thing kingdom manages
create table resources (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references users(id) on delete cascade,
  title text not null,
  description text,
  category_id uuid references categories(id),
  status text default 'available', -- available, reserved, archived
  metadata jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- categories for organizing resources
create table categories (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  parent_id uuid references categories(id), -- hierarchical categories
  created_at timestamptz default now()
);

-- connections between users and resources
create table connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  resource_id uuid references resources(id) on delete cascade,
  connection_type text not null, -- request, bookmark, share
  status text default 'pending', -- pending, accepted, rejected
  created_at timestamptz default now(),
  unique(user_id, resource_id, connection_type)
);
```

### why this structure

**uuids everywhere** instead of auto-increment integers. makes it harder to guess ids, easier to merge data if we ever need to, and works better with distributed systems.

**soft relationships via status fields** rather than hard deletes. when someone archives a resource, we keep the data. helps with analytics later and lets users undo mistakes.

**jsonb metadata field** on resources is the escape hatch. if someone needs to store something we didn't anticipate, it goes there. but the core structured data stays in proper columns.

**hierarchical categories** with self-referencing foreign key. simple but powerful. can represent "electronics > computers > laptops" without a separate table.

---

## api design

### rest endpoints

keeping it simple. standard rest with consistent patterns:

```
GET    /api/resources          - list resources (with filters)
GET    /api/resources/:id      - get single resource
POST   /api/resources          - create resource
PATCH  /api/resources/:id      - update resource
DELETE /api/resources/:id      - archive resource (soft delete)

GET    /api/users/me           - current user profile
PATCH  /api/users/me           - update profile

POST   /api/connections        - create connection request
PATCH  /api/connections/:id    - update connection status
GET    /api/connections        - list user's connections
```

### request/response patterns

every response follows the same shape:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "total": 42,
    "limit": 20
  }
}
```

errors look like:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "the requested resource does not exist"
  }
}
```

consistent structure means the frontend can have one error handler that works everywhere.

### filtering and pagination

resources endpoint supports:
- `?category=electronics` - filter by category slug
- `?status=available` - filter by status
- `?q=laptop` - full text search
- `?page=2&limit=20` - pagination
- `?sort=created_at&order=desc` - sorting

implemented with query builder that safely constructs sql:

```javascript
const buildResourceQuery = (filters) => {
  let query = 'select * from resources where 1=1';
  const params = [];
  
  if (filters.category) {
    params.push(filters.category);
    query += ` and category_id = (select id from categories where slug = $${params.length})`;
  }
  
  if (filters.status) {
    params.push(filters.status);
    query += ` and status = $${params.length}`;
  }
  
  if (filters.q) {
    params.push(`%${filters.q}%`);
    query += ` and (title ilike $${params.length} or description ilike $${params.length})`;
  }
  
  // pagination
  const limit = Math.min(filters.limit || 20, 100);
  const offset = ((filters.page || 1) - 1) * limit;
  params.push(limit, offset);
  query += ` limit $${params.length - 1} offset $${params.length}`;
  
  return { query, params };
};
```

---

## authentication flow

### how it works

1. user signs up with email/password
2. password gets hashed with bcrypt (cost factor 12)
3. on login, verify password and issue jwt access token (15 min) + refresh token (7 days)
4. access token goes in authorization header
5. refresh token stored in httponly cookie
6. when access token expires, frontend hits /api/auth/refresh
7. refresh rotation: every refresh issues new refresh token and invalidates old one

### token structure

```javascript
// access token payload
{
  sub: 'user-uuid',
  email: 'user@example.com',
  iat: 1737000000,
  exp: 1737000900 // 15 minutes
}

// refresh token stored in db
{
  id: 'token-uuid',
  user_id: 'user-uuid',
  token_hash: 'bcrypt-hash',
  expires_at: '2026-01-22T00:00:00Z',
  revoked: false
}
```

### why this approach

**short-lived access tokens** mean if one gets stolen, damage is limited to 15 minutes.

**refresh rotation** means stolen refresh tokens get detected. if attacker uses a refresh token, they get a new one. when the real user tries to refresh, their token is already used, we detect the conflict and revoke all tokens for that user.

**httponly cookies for refresh tokens** because javascript can't access them. xss attacks can't steal refresh tokens.

---

## frontend architecture

### component structure

```
src/
├── components/
│   ├── ui/              # generic reusable (button, input, modal)
│   ├── resources/       # resource-specific components
│   ├── connections/     # connection-specific components
│   └── layout/          # header, sidebar, page layouts
├── hooks/
│   ├── useAuth.ts       # authentication state and methods
│   ├── useResources.ts  # resource fetching and mutations
│   └── useConnections.ts
├── pages/
│   ├── Home.tsx
│   ├── Resources.tsx
│   ├── ResourceDetail.tsx
│   └── Profile.tsx
├── lib/
│   ├── api.ts           # axios instance with interceptors
│   ├── auth.ts          # token management
│   └── utils.ts
└── types/
    └── index.ts         # shared typescript types
```

### state management

no redux. using:
- **react-query** for server state (resources, connections, user data)
- **zustand** for client state (ui state, local preferences)

react-query handles caching, background refetching, optimistic updates. zustand is tiny and simple for the stuff that doesn't touch the server.

### api layer

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true, // for httponly cookies
});

// attach access token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const { data } = await api.post('/api/auth/refresh');
        localStorage.setItem('accessToken', data.accessToken);
        return api(originalRequest);
      } catch (refreshError) {
        // refresh failed, log user out
        localStorage.removeItem('accessToken');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

---

## current progress

### what's done
- database schema designed and migrated
- user auth flow working (signup, login, refresh, logout)
- basic crud for resources
- filtering and pagination on resources list
- frontend scaffolding and routing
- basic ui components

### what's in progress
- connections system (request, accept, reject flow)
- real-time notifications (considering websockets vs polling)
- search improvements (might add postgres full-text search or even elasticsearch later)

### what's next
- finish connections flow
- add email notifications for connection requests
- build out the dashboard/home page
- user onboarding flow
- mobile responsiveness

---

## challenges and decisions

### problem: n+1 queries on resource lists

when listing resources with their categories and owners, naive approach does:
1. fetch resources
2. for each resource, fetch category
3. for each resource, fetch owner

fixed with joins:

```sql
select 
  r.*,
  c.name as category_name,
  c.slug as category_slug,
  u.display_name as owner_name
from resources r
left join categories c on r.category_id = c.id
left join users u on r.owner_id = u.id
where r.status = 'available'
order by r.created_at desc
limit 20;
```

one query instead of 41.

### problem: race conditions on connection status

two users could theoretically accept the same resource simultaneously. solved with database constraints and transactions:

```sql
-- only one accepted connection per resource
create unique index one_accepted_connection 
on connections (resource_id) 
where status = 'accepted';
```

postgres enforces this at the database level. if two transactions try to accept simultaneously, one wins and one gets a constraint violation error which we handle gracefully.

### problem: password reset without email service yet

temporary solution: generate reset tokens, log them to console in dev, manual reset in production if needed. email integration is on the list but not blocking development.

---

## performance considerations

### indexes

```sql
create index idx_resources_owner on resources(owner_id);
create index idx_resources_category on resources(category_id);
create index idx_resources_status on resources(status);
create index idx_connections_user on connections(user_id);
create index idx_connections_resource on connections(resource_id);
```

### query optimization

using `explain analyze` liberally. caught a few slow queries early:
- added composite index for common filter combinations
- rewrote a subquery as a join
- added partial index for active resources only

### caching strategy

not implemented yet but planning:
- redis for session data and rate limiting
- react-query handles frontend caching
- cdn for static assets
- maybe edge caching for public resource lists

---

## testing approach

### backend tests

using jest + supertest for api tests:

```javascript
describe('POST /api/resources', () => {
  it('creates a resource for authenticated user', async () => {
    const token = await getTestUserToken();
    
    const res = await request(app)
      .post('/api/resources')
      .set('Authorization', `Bearer ${token}`)
      .send({
        title: 'test resource',
        description: 'test description',
        category_id: testCategoryId
      });
    
    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    expect(res.body.data.title).toBe('test resource');
  });
  
  it('rejects unauthenticated requests', async () => {
    const res = await request(app)
      .post('/api/resources')
      .send({ title: 'test' });
    
    expect(res.status).toBe(401);
  });
});
```

### frontend tests

vitest + react testing library for component tests. focusing on:
- user interactions work correctly
- error states display properly
- loading states show up
- forms validate input

not going crazy with coverage. testing the important paths, not every edge case.

---

## what i learned today

- writing raw sql is actually pretty pleasant when you have a good query builder
- jwt refresh rotation is more complex than it seems but worth it for security
- react-query eliminates so much boilerplate for data fetching
- database constraints are underrated. let postgres enforce your business rules
- n+1 queries sneak up on you fast. always check with explain

## tomorrow's plan

- finish the connections accept/reject flow
- add basic notification system
- start on the dashboard ui
- maybe look into websockets for real-time updates
- write more tests for auth edge cases

the foundation is solid. now it's about building out features and iterating based on feedback.
