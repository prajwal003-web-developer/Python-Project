
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  FiSearch,
  FiFileText,
  FiDownload,
  FiEye,
  FiLoader,
  FiAlertCircle,
} from "react-icons/fi";

import HomeLayout from "../../Components/Layouts/HomeLayout";
import api from "../../Lib/api";

const Search = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const searchQuery = searchParams.get("q")?.trim();

    if (!searchQuery) {
      setNotes([]);
      setError("");
      setLoading(false);
      return;
    }

    let active = true;

    const searchNotes = async () => {
      setLoading(true);
      setError("");

      try {
        // Public search: no authorization token required.
        const response = await api.get("/notes/search", {
          params: { q: searchQuery },
        });

        const data = response.data;

        const results = Array.isArray(data)
          ? data
          : data?.notes || data?.results || data?.data || [];

        if (active) {
          setNotes(results);
        }
      } catch (err) {
        if (active) {
          setNotes([]);
          setError(
            err.response?.data?.detail ||
              "Unable to search notes. Please try again."
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    searchNotes();

    return () => {
      active = false;
    };
  }, [searchParams]);

  const handleSubmit = (event) => {
    event.preventDefault();

    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setSearchParams({});
      setNotes([]);
      return;
    }

    setSearchParams({ q: trimmedQuery });
  };

  const getFileUrl = (note) =>
    note.file_url ||
    note.fileUrl ||
    note.cloudinary_url ||
    note.url ||
    "";

  const getNoteId = (note) =>
    note.id || note._id;

  return (
   <HomeLayout>
     <main className="min-h-screen bg-slate-50 px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8">
          <p className="mb-3 text-sm font-bold tracking-widest text-cyan-700">
            EDUNOTES / SEARCH
          </p>

          <h1 className="text-3xl font-black tracking-tight text-slate-900 sm:text-4xl">
            Find your study materials
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-500 sm:text-base">
            Search notes by title, subject, faculty, or programme.
            Browse and access available academic resources.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="mb-8 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm sm:flex-row"
        >
          <div className="flex flex-1 items-center gap-3 px-3">
            <FiSearch className="shrink-0 text-xl text-slate-400" />

            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search notes, subjects, programmes..."
              aria-label="Search notes"
              className="w-full bg-transparent py-3 text-sm text-slate-800 outline-none placeholder:text-slate-400"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-700 px-6 py-3 text-sm font-bold text-white transition hover:bg-cyan-800 disabled:opacity-60"
          >
            <FiSearch size={18} />
            Search
          </button>
        </form>

        {searchParams.get("q") && (
          <div className="mb-5 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-lg font-bold text-slate-800">
              Results for "{searchParams.get("q")}"
            </h2>

            {!loading && !error && (
              <span className="text-sm text-slate-500">
                {notes.length} {notes.length === 1 ? "note" : "notes"} found
              </span>
            )}
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white px-5 py-16 text-center">
            <FiLoader className="mb-4 animate-spin text-3xl text-cyan-700" />
            <p className="font-semibold text-slate-700">
              Searching notes...
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Please wait while we find matching materials.
            </p>
          </div>
        )}

        {!loading && error && (
          <div
            role="alert"
            className="flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-5 text-sm text-red-700"
          >
            <FiAlertCircle className="mt-0.5 shrink-0 text-lg" />
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && !searchParams.get("q") && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-16 text-center">
            <FiSearch className="mx-auto mb-4 text-4xl text-slate-300" />
            <h2 className="text-lg font-bold text-slate-800">
              What are you studying?
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Enter a subject, note title, or programme to get started.
            </p>
          </div>
        )}

        {!loading &&
          !error &&
          searchParams.get("q") &&
          notes.length === 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white px-5 py-16 text-center">
              <FiFileText className="mx-auto mb-4 text-4xl text-slate-300" />
              <h2 className="text-lg font-bold text-slate-800">
                No notes found
              </h2>
              <p className="mt-2 text-sm text-slate-500">
                Try another keyword or check your spelling.
              </p>
            </div>
          )}

        {!loading && !error && notes.length > 0 && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {notes.map((note, index) => {
              const fileUrl = note.file.url

             

              return (
                <article
                  key={getNoteId(note) || index}
                  className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                >
                  <div className="mb-4 flex items-start gap-3">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700">
                      <FiFileText size={24} />
                    </div>

                    <div className="min-w-0 flex-1">
                      <h3 className="break-words font-bold text-slate-900">
                        {note.title || note.name || "Untitled note"}
                      </h3>

                      <p className="mt-1 text-xs text-slate-500">
                        {note.subject || "Academic material"}
                      </p>
                    </div>
                  </div>

                  <p className="mb-4 line-clamp-3 flex-1 text-sm leading-6 text-slate-600">
                    {note.description || "No description available."}
                  </p>
{/* 
                  <div className="mb-4 space-y-1 text-xs text-slate-500">
                    {(note.faculty_name || note.faculty) && (
                      <p>
                        Faculty:{" "}
                        {typeof note.faculty === "object"
                          ? note.faculty.name
                          : note.faculty_name || note.faculty}
                      </p>
                    )}

                    {(note.programme_name || note.programme) && (
                      <p>
                        Programme:{" "}
                        {typeof note.programme === "object"
                          ? note.programme.name
                          : note.programme_name || note.programme}
                      </p>
                    )}

                    {(note.semester || note.year) && (
                      <p>
                        {note.semester
                          ? `Semester: ${note.semester}`
                          : `Year: ${note.year}`}
                      </p>
                    )}
                  </div> */}

                  <div className="flex gap-3 border-t border-slate-100 pt-4">
                    <button
                      type="button"
                      onClick={() => {
                        if (fileUrl) {
                          window.open(fileUrl, "_blank", "noopener,noreferrer");
                        }
                      }}
                      disabled={!fileUrl}
                      className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <FiEye size={16} />
                      View
                    </button>

                    <a
                      href={fileUrl || undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      aria-disabled={!fileUrl}
                      onClick={(event) => {
                        if (!fileUrl) event.preventDefault();
                      }}
                      className={`inline-flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold text-white transition ${
                        fileUrl
                          ? "bg-cyan-700 hover:bg-cyan-800"
                          : "cursor-not-allowed bg-slate-300"
                      }`}
                    >
                      <FiDownload size={16} />
                      Download
                    </a>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </main>
   </HomeLayout>
  );
};

export default Search;
