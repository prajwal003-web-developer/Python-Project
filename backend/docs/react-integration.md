# React integration guide

The backend uses **HttpOnly cookies** (access + refresh) and a **CSRF header**. React never sees or stores
the JWTs. It only keeps a CSRF token in memory and sends it on write requests.

* Public endpoints (faculties, departments, notes, profiles) work with no login.
* Every JSON field is **camelCase**. Errors are always `{ "error": { "code", "message", "details?" } }`.
* Frontend `.env`:  `VITE_API_URL=http://localhost:8000/api`  (Create React App: `REACT_APP_API_URL`)
* Backend `.env` must list your frontend origin: `FRONTEND_ORIGINS=http://localhost:5173`

## 1. Shared API client — `src/api/client.js`

```js
import axios from "axios";

let csrfToken = null;
export const setCsrfToken = (t) => { csrfToken = t; };

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,   // e.g. http://localhost:8000/api
  withCredentials: true,                   // REQUIRED: sends/receives the auth cookies
});

// Send the CSRF token on every state-changing request.
api.interceptors.request.use((config) => {
  const method = (config.method || "get").toLowerCase();
  if (csrfToken && !["get", "head", "options"].includes(method)) {
    config.headers["X-CSRF-Token"] = csrfToken;
  }
  return config;
});

// If the 15-minute access token expired, refresh once and retry the original request.
let refreshing = null;
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const { config, response } = error;
    const isAuthCall = config?.url?.startsWith("/auth/");
    if (response?.status === 401 && config && !config._retried && !isAuthCall) {
      config._retried = true;
      refreshing ??= api.post("/auth/refresh")
        .then((r) => setCsrfToken(r.data.csrfToken))
        .finally(() => { refreshing = null; });
      try {
        await refreshing;
        return api(config);
      } catch { /* refresh failed: the caller sees the original 401 */ }
    }
    return Promise.reject(error);
  }
);

export const apiError = (err) =>
  err.response?.data?.error ?? { code: "network_error", message: "Cannot reach the server" };

export default api;
```

## 2. Logged-in user and role — `src/context/AuthContext.jsx`

```jsx
import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api, { setCsrfToken } from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);       // { id, name, username, email, role, ... } | null
  const [loading, setLoading] = useState(true);

  // On every page load: restore the CSRF token, then ask the server who we are.
  useEffect(() => {
    (async () => {
      try {
        setCsrfToken((await api.get("/auth/csrf")).data.csrfToken);
        setUser((await api.get("/auth/me")).data);
      } catch (e) {
        if (e.response?.status === 401) {          // access token expired -> try the refresh cookie
          try {
            const { data } = await api.post("/auth/refresh");
            setCsrfToken(data.csrfToken);
            setUser(data.user);
          } catch { setUser(null); }
        }
      } finally { setLoading(false); }
    })();
  }, []);

  const login = useCallback(async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    setCsrfToken(data.csrfToken);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try { await api.post("/auth/logout"); } finally { setUser(null); }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser,
      isUploader: user?.role === "uploader", isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
}
```

Route guard (UX only — the **backend** enforces the real permissions):

```jsx
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RequireRole({ roles }) {         // <RequireRole roles={["uploader"]} />
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return null;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <Outlet />;
}
```

## 3. Which page calls what

| Frontend page | Calls |
|---|---|
| Faculties listing | `GET /faculties` |
| Department listing | `GET /departments?facultyId=…` |
| Semester selection | static 1–8, then `GET /notes?departmentId=…&semester=3` |
| Notes listing | `GET /notes?…` (§4) |
| `ShowingFiles.jsx` | `GET /notes/{id}`; open `note.fileUrl` in a new tab |
| Saved Notes | `GET /saved-notes`, `POST/DELETE /saved-notes/{id}` |
| Register / Login | `POST /auth/register`, `POST /auth/login` |
| Uploader dashboard | `GET /notes/mine`, `DELETE /notes/{id}` |
| Upload / edit form | `POST /notes` (multipart), `PATCH /notes/{id}`, `PUT /notes/{id}/file` |
| Public uploader page | `GET /users/{username}/public`, `GET /users/{username}/notes` |
| Request a department | `POST /departments/requests`, `GET /departments/requests/mine` |
| Admin dashboard | `GET /admin/dashboard`, `GET /admin/users`, `PATCH /admin/users/{id}/role` |
| Department request management | `GET /admin/department-requests?status=pending`, `PATCH …/{id}/approve`, `PATCH …/{id}/reject` |

## 4. Example requests and responses

### Register / login
```js
await api.post("/auth/register", { name, username, email, password, confirmPassword });
const user = await login(email, password);
```
`POST /auth/register` → **201**
```json
{ "id": "66f1…", "name": "Alice Doe", "username": "alice", "email": "alice@example.com",
  "role": "user", "isActive": true, "createdAt": "2026-10-25T10:00:00Z", "updatedAt": "2026-10-25T10:00:00Z" }
```
`POST /auth/login` → **200** (also sets the HttpOnly cookies)
```json
{ "user": { "id": "66f1…", "name": "Alice Doe", "username": "alice", "email": "alice@example.com",
            "role": "user", "isActive": true, "createdAt": "…", "updatedAt": "…" },
  "csrfToken": "q3x…" }
```
Validation error → **422**
```json
{ "error": { "code": "validation_error", "message": "Request validation failed",
    "details": [ { "field": "password", "message": "Password must contain a digit" } ] } }
```
Duplicate → **409** `{ "error": { "code": "duplicate_account", …, "details": [ { "field": "email", "message": "This email is already registered" } ] } }`

### Paginated note search (public, no login)
```js
const { data } = await api.get("/notes", {
  params: { q: "algorithms", departmentId, semester: 3, fileType: "pdf",
            page: 1, limit: 12, sortBy: "createdAt", sortOrder: "desc" },
});
```
Parameters: `q` (title/description/subject), `facultyId`, `departmentId`, `semester`, `username`, `fileType` (`pdf|docx`),
`page` (≥1), `limit` (1–50), `sortBy` (`createdAt|updatedAt|title`), `sortOrder` (`asc|desc`).
```json
{ "items": [ {
    "id": "66f2…", "title": "Algorithms Handbook", "description": "sorting", "subject": "Algorithms",
    "facultyId": "66e0…", "facultyName": "Engineering", "departmentId": "66e1…", "departmentName": "Computer Science",
    "semester": 3, "fileType": "pdf", "fileUrl": "https://res.cloudinary.com/…/raw/upload/…pdf", "fileSize": 482113,
    "isPublished": true, "hiddenByAdmin": false,
    "uploader": { "name": "Uploader One", "username": "uploader1" },
    "createdAt": "…", "updatedAt": "…" } ],
  "page": 1, "limit": 12, "total": 37, "totalPages": 4 }
```
Open / download a note (`ShowingFiles.jsx`):
```jsx
<a href={note.fileUrl} target="_blank" rel="noopener noreferrer">Open / Download</a>
```

### Upload a note (uploader) — multipart
```js
const form = new FormData();
form.append("title", title);
form.append("subject", subject);
form.append("description", description);
form.append("facultyId", facultyId);
form.append("departmentId", departmentId);
form.append("semester", String(semester));
form.append("file", fileInput.files[0]);          // .pdf or .docx
// Do NOT set Content-Type yourself; the browser adds the multipart boundary.
const { data: note } = await api.post("/notes", form);
```
→ **201** with the note object above. Errors: `401` not logged in, `403 uploader_required`,
`404 faculty_not_found / department_not_found`, `413 file_too_large`,
`415 unsupported_file_type / invalid_pdf / invalid_docx / mime_mismatch`, `400 empty_file`, `422 validation_error`.

### Edit, replace, delete
```js
await api.patch(`/notes/${id}`, { title, description, subject, semester, facultyId, departmentId, isPublished });
const f = new FormData(); f.append("file", newFile);
await api.put(`/notes/${id}/file`, f);
await api.delete(`/notes/${id}`);
```

### Uploader dashboard — `GET /notes/mine?q=&fileType=&page=&limit=`
```json
{ "stats": { "totalNotes": 12, "publishedNotes": 11, "unpublishedNotes": 1, "pdfCount": 9, "docxCount": 3,
             "totalFileSize": 18234567, "firstUploadedAt": "…", "lastUploadedAt": "…" },
  "notes": { "items": [ ], "page": 1, "limit": 20, "total": 12, "totalPages": 1 } }
```

### Saved notes
```js
await api.post(`/saved-notes/${noteId}`);   // 201 newly saved, 200 already saved -> { "noteId": "…", "saved": true }
await api.delete(`/saved-notes/${noteId}`); // always 200 -> { "noteId": "…", "saved": false }
const { data } = await api.get("/saved-notes", { params: { page: 1, limit: 20 } });
// { items: [ { savedAt: "…", note: { …note object… } } ], page, limit, total, totalPages }
```
Show the save button to everyone; when `user` is null send them to `/login` instead of calling the API.

### Public uploader profile — `GET /users/uploader1/public?page=1&limit=12`
```json
{ "name": "Uploader One", "username": "uploader1", "publicUploadCount": 12,
  "notes": { "items": [ ], "page": 1, "limit": 12, "total": 12, "totalPages": 1 } }
```

### Department requests
```js
await api.post("/departments/requests", { name: "Biotechnology", facultyId, description: "…" });   // 201, status "pending"
await api.get("/departments/requests/mine");
// admin
await api.get("/admin/department-requests", { params: { status: "pending", page: 1 } });
await api.patch(`/admin/department-requests/${id}/approve`, { adminComment: "Approved" });
await api.patch(`/admin/department-requests/${id}/reject`,  { adminComment: "Duplicate" });
```

### Admin dashboard — `GET /admin/dashboard`
```json
{ "counts": { "users": 120, "uploaders": 8, "admins": 1, "notes": 340, "publishedNotes": 336,
              "faculties": 4, "departments": 12, "pendingDepartmentRequests": 2 },
  "recentActivity": [ { "id": "…", "action": "department_request.approve", "actorId": "…", "actorUsername": "siteadmin",
                        "targetType": "department_request", "targetId": "…", "metadata": { "name": "Biotechnology" },
                        "createdAt": "…" } ] }
```
Role change: ``api.patch(`/admin/users/${id}/role`, { role: "uploader" })`` (`user | uploader | admin`).
Status: ``api.patch(`/admin/users/${id}/status`, { isActive: false })``.

## 5. Status codes to handle

`400` bad id / empty file · `401` not logged in (the client tries `/auth/refresh` once) · `403` wrong role, CSRF failure,
disabled account, not the owner · `404` not found · `409` duplicate / conflict (last admin, department has notes) ·
`413` file too large · `415` wrong file type · `422` validation · `429` rate limited (`Retry-After` header) ·
`502` storage (Cloudinary) problem.
