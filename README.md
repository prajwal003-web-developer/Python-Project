# ADTU Notes 📚

A full-stack academic notes-sharing platform built to help students discover, view, and download study materials organized by faculty, programme, semester, and subject.

ADTU Notes provides a centralized platform for academic resources, allowing students to access notes publicly while registered users can upload and manage their own materials.

## ✨ Features

### Public Features
- Browse academic notes without logging in.
- Explore notes by faculty, programme, semester, and subject.
- Search notes by title, description, subject, and uploaded filename.
- View and download available study materials.
- Access file information, including filename, format, and size.
- View faculty and programme details associated with notes.

### Authentication
- User registration and login.
- JWT-based authentication.
- Password hashing.
- Protected endpoints for authenticated users.
- Access-controlled note management.

### Notes Management
- Upload PDF, DOCX, PPT, and PPTX files.
- Add a title, description, faculty, programme, semester, and subject.
- Store uploaded files in Cloudinary.
- Store file metadata and note information in MongoDB.
- Delete your own uploaded notes.
- Prevent users from deleting notes uploaded by other users.

### Saved Notes
- Save notes to a personal collection.
- Remove notes from saved notes.
- Retrieve saved notes after authentication.
- Browse and search public notes without an account.

### Administration
- Manage faculties and programmes.
- Support department/programme requests and administrative approval, where implemented.
- Protect administrative operations from unauthorized access.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js |
| Frontend tooling | Vite |
| Styling | CSS / Tailwind CSS, depending on the implemented components |
| API communication | Axios |
| Backend | Python, FastAPI |
| Database | MongoDB |
| MongoDB driver | PyMongo AsyncMongoClient |
| File storage | Cloudinary |
| Authentication | JWT |
| Password security | Argon2 or the password-hashing implementation configured in the backend |
| API documentation | FastAPI Swagger UI |
| Frontend deployment | Vercel |
| Backend deployment | Render |
| Version control | Git and GitHub |

## 📁 Project Structure

The following is a suggested root layout. Keep your existing filenames and folders if they differ.

```text
ADTU_NOTES/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── stores/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── router.py
│   │   ├── controllers/
│   │   ├── db/
│   │   │   ├── mongodb.py
│   │   │   └── cloudinary.py
│   │   ├── endpoints/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
│
├── README.md
└── .gitignore
```

## ⚙️ Prerequisites

Install the following before running the project:

- Git
- Node.js and npm
- Python 3.12 recommended
- MongoDB Atlas account or a compatible MongoDB deployment
- Cloudinary account

Python 3.12 is a suitable starting point for this project and avoids some dependency build issues encountered with newer Python versions.

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/prajwal003-web-developer/Python-Project.git
cd Python-Project
```

If your ADTU Notes project is in a different repository, replace the URL with that repository's address.

### 2. Configure the backend

Open the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python3.12 -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is empty or missing dependencies, add the packages required by your implementation, including FastAPI, Uvicorn, PyMongo, Pydantic Settings, Cloudinary, PyJWT, Argon2, and `python-multipart`.

### 3. Configure environment variables

Create a `.env` file inside `backend/`.

```env
MONGODB_URL=mongodb+srv://<username>:<password>@<cluster-host>/
DATABASE_NAME=adtu_notes

JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Replace the placeholders with your actual configuration values.

**Important security rules:**
- Never commit `.env` to GitHub.
- Never expose your MongoDB password or Cloudinary API secret in React.
- Keep JWT secrets on the backend.
- If credentials have been exposed publicly, rotate them.
- Configure MongoDB Atlas network access and database-user permissions correctly.

### 4. Run the backend

From the `backend/` directory, start FastAPI:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API should now be available at:

- API base URL: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

The application should connect to MongoDB and create the configured indexes during startup.

If your `main.py` is located directly in the backend root instead of `backend/app/`, adjust the Uvicorn import path accordingly.

### 5. Configure the React frontend

Open a second terminal and navigate to the frontend:

```bash
cd frontend
npm install
```

Create a `.env` file in `frontend/`:

```env
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

This assumes the FastAPI router is mounted at `/api/v1` and your Axios instance uses `VITE_API_URL` as its base URL.

For example:

```javascript
import axios from "axios";

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000/api/v1",
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("Token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
```

Keep this example aligned with your existing `api.js`. If your authentication flow uses cookies instead of bearer tokens, configure Axios and the backend accordingly. For multipart uploads, let Axios/browser set the multipart content type and boundary automatically.

### 6. Run the frontend

```bash
npm run dev
```

Open the local URL displayed by Vite, usually:

```text
http://localhost:5173
```

You should now be able to use the frontend and backend together.

## 🔌 API Overview

All routes below assume the backend uses the `/api/v1` prefix. The route paths shown for upload, search, and note listing reflect the implemented endpoints; verify authentication, faculty, programme, and administrative paths against your router.

### Public Notes

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/notes/` | List notes for a programme and semester |
| GET | `/api/v1/notes/search?q=python` | Search notes publicly |

Example: retrieve notes for a programme and semester.

```http
GET /api/v1/notes/?programme_id=PROGRAMME_ID&semester=2
```

Example: search notes without logging in.

```http
GET /api/v1/notes/search?q=python
```

Search results can include note details, file metadata, programme information, and faculty information when those references are correctly stored and resolved.

### Authentication

The backend provides authenticated operations through its authentication controller and endpoints.

Typical operations include:

- Register an account.
- Log in and receive an authentication token.
- Retrieve the authenticated user's information.
- Access protected routes using the configured authentication dependency.

Use the actual paths exposed by your authentication router and the Swagger documentation.

### Upload Notes

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/v1/upload/notes` | Authenticated users |

The upload endpoint accepts multipart form data.

| Field | Description |
|---|---|
| `file` | PDF, DOCX, PPT, or PPTX file |
| `title` | Note title |
| `description` | Note description |
| `faculty` | Faculty reference |
| `programme` | Programme reference |
| `semester` | Semester identifier |
| `subject` | Subject name |

Example using JavaScript:

```javascript
const formData = new FormData();

formData.append("file", file);
formData.append("title", title);
formData.append("description", description);
formData.append("faculty", facultyId);
formData.append("programme", programmeId);
formData.append("semester", semester);
formData.append("subject", subject);

const response = await api.post(
  "/upload/notes",
  formData
);
```

The backend validates the file, uploads it to Cloudinary, saves file metadata in MongoDB, and creates a note record.

The backend currently shown in the upload controller allows PDF, DOCX, PPT, and PPTX files with a maximum size of 10 MB. Keep this limit consistent with your frontend validation and deployment configuration.

### Delete an Uploaded Note

| Method | Endpoint | Access |
|---|---|---|
| DELETE | `/api/v1/upload/notes/{note_id}` | Authenticated uploader |

Example:

```javascript
await api.delete(`/upload/notes/${noteId}`);
```

The backend verifies the uploader before allowing deletion. A user cannot delete another user's note simply by knowing its ID.

The implementation also attempts to remove the associated Cloudinary file and MongoDB file metadata when they are no longer referenced by another note.

### Saved Notes

The notes router includes these operations:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/notes/saved` | Retrieve saved notes |
| POST | `/api/v1/notes/{note_id}/save` | Save a note |
| DELETE | `/api/v1/notes/{note_id}/save` | Remove a saved note |

These operations require authentication.

### Faculties, Programmes, and Administration

Faculty, programme, and administrative routes depend on the endpoints included in your API router.

Check `app/api/router.py` and `http://127.0.0.1:8000/docs` for the exact paths and HTTP methods available in your current implementation.

## ☁️ File Storage with Cloudinary

ADTU Notes stores document files in Cloudinary and file metadata in MongoDB.

The upload flow is:

1. An authenticated user submits a document.
2. FastAPI validates the filename, extension, and file size.
3. Cloudinary stores the file.
4. MongoDB stores the file URL, original filename, size, format, uploader, and upload timestamp.
5. MongoDB stores the note details and the associated file ID.
6. Public note and search endpoints resolve the file metadata for frontend viewing and downloading.

### Cloudinary PDF Delivery

If a PDF upload succeeds but opening its URL returns `401 Unauthorized`, check Cloudinary's delivery and access-control settings.

For publicly accessible study materials, configure delivery to allow public access to the intended resources. Do not expose private or restricted documents by disabling security controls indiscriminately.

Use the `secure_url` returned by Cloudinary rather than manually constructing the URL. Confirm that the returned URL works in a private browser window if the resource is intended to be public.

## 🌐 Deployment

### Deploy the backend on Render

1. Push the project to GitHub.
2. Create a new Web Service in Render.
3. Select the repository and configure the backend root directory as `backend` if your repository is organized into separate `frontend/` and `backend/` folders.
4. Set the build and start commands.

**Build Command**

```bash
pip install -r requirements.txt
```

**Start Command**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Add all required backend environment variables in Render.
6. Deploy the service.
7. Check the deployment logs for successful startup and MongoDB connection.
8. Open the deployed API's `/docs` endpoint to verify the service.

Binding to `0.0.0.0` and using Render's `$PORT` environment variable allows Render to detect the listening web service.

If the deployment reports that no ports are open, verify the start command, application import path, and startup errors.

### Configure CORS

Your FastAPI backend must allow requests from the deployed frontend origin.

For example, configure the middleware in `app/main.py` with your actual frontend URL:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Replace `https://your-frontend.vercel.app` with your real deployed frontend origin. Do not use a wildcard origin with credentialed requests.

### Deploy the frontend on Vercel

1. Import the repository into Vercel.
2. Select the `frontend` directory as the project root if needed.
3. Configure the build command as `npm run build`.
4. Set the output directory to `dist` for a standard Vite application.
5. Add the frontend environment variable:

```env
VITE_API_URL=https://your-backend.onrender.com/api/v1
```

6. Deploy the project.
7. Test registration, login, public search, file viewing, uploads, saved notes, and deletion.

Vite environment variables prefixed with `VITE_` are exposed to frontend code. Never put database credentials, JWT signing secrets, or Cloudinary API secrets in them.

## 🧪 Testing Checklist

Before considering the application ready, verify the following:

- [ ] The React frontend starts successfully.
- [ ] FastAPI starts successfully.
- [ ] MongoDB connects and indexes are created.
- [ ] Registration and login work.
- [ ] Public note browsing works without authentication.
- [ ] Public search returns relevant notes.
- [ ] Faculty and programme details appear correctly.
- [ ] PDF and Office document URLs work as intended.
- [ ] Authenticated users can upload valid documents.
- [ ] Invalid extensions and oversized files are rejected.
- [ ] Users can save and unsave notes.
- [ ] Users can delete their own notes.
- [ ] Users cannot delete another user's notes.
- [ ] CORS works on the deployed frontend.
- [ ] Render binds to `0.0.0.0` on the assigned port.
- [ ] Secrets are not committed to the repository.

## 🛡️ Security Considerations

- Store secrets in environment variables.
- Hash passwords securely.
- Validate all user input on the backend.
- Verify JWTs on protected routes.
- Enforce uploader ownership on deletion and editing.
- Validate uploaded files on the server, not only in React.
- Restrict file size and supported file types.
- Configure MongoDB permissions and network access appropriately.
- Do not return sensitive user information in public API responses.
- Treat Cloudinary URLs according to the intended visibility of the files.
- Log server-side errors without exposing secrets or internal tracebacks to clients.

## 🐛 Troubleshooting

### MongoDB connection fails

- Check `MONGODB_URL` and `DATABASE_NAME`.
- Confirm the database user's credentials.
- Check Atlas network access rules.
- Ensure your environment variables are loaded correctly.

### Cloudinary returns 401 when opening a file

- Check delivery restrictions and resource access settings.
- Verify the stored `secure_url`.
- Inspect the failed request's `X-Cld-Error` response header.
- Confirm that the document is meant to be publicly accessible.

### Render reports no open ports

Use:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Confirm that `app.main:app` matches your project structure and that startup completes successfully.

### Frontend API requests fail

- Verify `VITE_API_URL`.
- Confirm the deployed backend is running.
- Check CORS configuration.
- Inspect the browser's Network tab for the actual API URL and response.
- Confirm that protected endpoints receive the expected authentication token.

### Notes return ObjectIds instead of programme or faculty names

MongoDB references do not automatically become populated objects. Resolve the referenced programme and faculty documents in the backend and serialize their IDs as strings before returning JSON.

## 📌 Future Improvements

- Pagination for large note collections.
- Advanced filtering by faculty, programme, semester, and subject.
- Better search indexing for larger datasets.
- Note previews and document metadata extraction.
- Administrative dashboards and moderation.
- User profiles and uploader attribution.
- Automated tests for authorization and file handling.
- Improved observability and error reporting.

## 👨‍💻 Author

**Prajwal Neupane**

- GitHub: [prajwal003-web-developer](https://github.com/prajwal003-web-developer)
- Portfolio: [prajwalneupane.vercel.app](https://prajwalneupane.vercel.app)

## 📄 License

Choose and add a license before distributing the project publicly. If no license has been added, all rights remain reserved by the copyright holder.

---

Built to make academic resources easier to discover, share, and access.
