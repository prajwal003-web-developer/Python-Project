
import { useCallback, useEffect, useState } from "react";
import {
  FiBookOpen,
  FiDownload,
  FiExternalLink,
  FiFileText,
  FiLoader,
  FiRefreshCw,
  FiSearch,
  FiTrash2,
  FiUploadCloud,
} from "react-icons/fi";
import { Link } from "react-router-dom";

import "./MyNotes.css";
import AuthorizedLayout from "../Authorized/Layouts/AuthorizedLayout";
import api from "../../Lib/api";

function formatDate(date) {
  if (!date) return "Date unavailable";

  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return "Date unavailable";
  }

  return parsedDate.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatFileSize(bytes) {
  const size = Number(bytes);

  if (!Number.isFinite(size) || size <= 0) return "";

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(0)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

function getFileType(note) {
  return (
    note.format ||
    note.filename?.split(".").pop()?.toUpperCase() ||
    "FILE"
  ).toUpperCase();
}

export default function MyNotes() {
  const [notes, setNotes] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const fetchMyNotes = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/upload/my-notes");
      setNotes(response.data.notes ?? []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Couldn't load your notes. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMyNotes();
  }, [fetchMyNotes]);

  const handleDelete = async (note) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${note.title}"?`
    );

    if (!confirmed) return;

    setDeletingId(note.id);
    setError("");

    try {
      await api.delete(`/upload/notes/${note.id}`);
      setNotes((currentNotes) =>
        currentNotes.filter((item) => item.id !== note.id)
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Couldn't delete this note. Please try again."
      );
    } finally {
      setDeletingId(null);
    }
  };

  const filteredNotes = notes.filter((note) => {
    const query = search.trim().toLowerCase();

    if (!query) return true;

    return [
      note.title,
      note.subject,
      note.filename,
      note.semester,
    ].some((value) => String(value ?? "").toLowerCase().includes(query));
  });

  return (
    <AuthorizedLayout>
        <main className="my-notes-page">
      <section className="my-notes-container">
        <header className="my-notes-header">
          <div className="my-notes-heading">
            <div className="my-notes-heading-icon">
              <FiBookOpen />
            </div>

            <div>
              <p className="my-notes-eyebrow">YOUR PERSONAL LIBRARY</p>
              <h1>My Notes</h1>
              <p className="my-notes-subtitle">
                Manage the study materials you've shared on ADTU Notes.
              </p>
            </div>
          </div>

          <Link to="/add" className="my-notes-upload-button">
            <FiUploadCloud />
            <span>Upload a note</span>
          </Link>
        </header>

        <section className="my-notes-toolbar">
          <div className="my-notes-count">
            <span className="my-notes-count-icon">
              <FiFileText />
            </span>
            <div>
              <strong>{notes.length}</strong>
              <span>{notes.length === 1 ? "Uploaded note" : "Uploaded notes"}</span>
            </div>
          </div>

          <label className="my-notes-search">
            <FiSearch />
            <input
              type="search"
              placeholder="Search title, subject, filename..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
        </section>

        {error && (
          <div className="my-notes-error" role="alert">
            <span>{error}</span>
            <button type="button" onClick={fetchMyNotes}>
              Try again
            </button>
          </div>
        )}

        {loading ? (
          <div className="my-notes-state">
            <FiLoader className="my-notes-spinner" />
            <h2>Loading your notes</h2>
            <p>Gathering your uploaded study materials...</p>
          </div>
        ) : notes.length === 0 ? (
          <div className="my-notes-state">
            <div className="my-notes-empty-icon">
              <FiBookOpen />
            </div>
            <h2>Your library is waiting</h2>
            <p>
              You haven't uploaded any notes yet. Share your first study
              material and find it here whenever you need it.
            </p>
            <Link to="/upload" className="my-notes-primary-button">
              <FiUploadCloud />
              Upload your first note
            </Link>
          </div>
        ) : filteredNotes.length === 0 ? (
          <div className="my-notes-state my-notes-compact-state">
            <FiSearch className="my-notes-state-icon" />
            <h2>No matching notes</h2>
            <p>Try another title, subject, or filename.</p>
            <button
              type="button"
              className="my-notes-secondary-button"
              onClick={() => setSearch("")}
            >
              Clear search
            </button>
          </div>
        ) : (
          <>
            <div className="my-notes-results-heading">
              <h2>Your uploads</h2>
              <button
                type="button"
                className="my-notes-refresh-button"
                onClick={fetchMyNotes}
                disabled={loading}
              >
                <FiRefreshCw />
                Refresh
              </button>
            </div>

            <div className="my-notes-grid">
              {filteredNotes.map((note) => (
                <article className="my-note-card" key={note.id}>
                  <div className="my-note-card-top">
                    <div className="my-note-file-icon">
                      <FiFileText />
                    </div>
                    <span className="my-note-file-type">
                      {getFileType(note)}
                    </span>
                  </div>

                  <div className="my-note-content">
                    <h3 title={note.title}>{note.title || "Untitled note"}</h3>

                    <p className="my-note-subject">
                      {note.subject || "Subject not specified"}
                    </p>

                    <div className="my-note-file-name" title={note.filename}>
                      <FiFileText />
                      <span>{note.filename || "Original filename unavailable"}</span>
                    </div>

                    <div className="my-note-meta">
                      <span>{formatDate(note.created_at)}</span>
                      {formatFileSize(note.size) && (
                        <>
                          <span className="my-note-meta-dot">•</span>
                          <span>{formatFileSize(note.size)}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="my-note-actions">
                    {note.file_url ? (
                      <>
                        <a
                          className="my-note-open-button"
                          href={note.file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <FiExternalLink />
                          Open file
                        </a>

                        <a
                          className="my-note-download-button"
                          href={note.file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`Open ${note.filename || note.title}`}
                          title="Open file in a new tab"
                        >
                          <FiDownload />
                        </a>
                      </>
                    ) : (
                      <span className="my-note-unavailable">
                        File link unavailable
                      </span>
                    )}

                    <button
                      type="button"
                      className="my-note-delete-button"
                      onClick={() => handleDelete(note)}
                      disabled={deletingId === note.id}
                      aria-label={`Delete ${note.title}`}
                      title="Delete note"
                    >
                      {deletingId === note.id ? (
                        <FiLoader className="my-notes-spinner" />
                      ) : (
                        <FiTrash2 />
                      )}
                    </button>
                  </div>
                </article>
              ))}
            </div>

            <p className="my-notes-footer">
              Showing {filteredNotes.length} of {notes.length} notes
            </p>
          </>
        )}
      </section>
    </main>
    </AuthorizedLayout>
  );
}
