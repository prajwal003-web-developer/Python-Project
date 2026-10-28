
import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  FiArrowLeft,
  FiBookOpen,
  FiFileText,
  FiRefreshCw,
  FiAlertCircle,
} from "react-icons/fi";
import HomeLayout from "../../Components/Layouts/HomeLayout";
import ShowingFiles from "../../Components/ShowingFiles";
import api from "../../Lib/api";

;

const Notes = () => {
  const { facultyId, departmentId, semester } = useParams();

  const facultyNames = {
    engineering: "Engineering",
    science: "Science",
    management: "Management",
    humanities: "Humanities",
  };

  const departmentNames = {
    cse: "Computer Science & Engineering",
    it: "Information Technology",
    civil: "Civil Engineering",
    mechanical: "Mechanical Engineering",
    electrical: "Electrical Engineering",
    physics: "Physics",
    chemistry: "Chemistry",
    mathematics: "Mathematics",
    business: "Business Administration",
    commerce: "Commerce",
    english: "English",
    economics: "Economics",
  };

  const facultyName = facultyNames[facultyId] || facultyId;
  const departmentName =
    departmentNames[departmentId] || departmentId;

  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingIds, setSavingIds] = useState({});

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      // Public endpoint: no login required.
      const response = await api.get("/notes/", {
        params: {
          programme_id: departmentId,
          semester,
        },
      });

      const fetchedNotes = response.data?.notes || [];

      console.log(fetchedNotes);
      // Try to get saved notes. This request requires login,
      // but failure must not prevent public notes from displaying.
      let savedIds = new Set();

      try {
        const savedResponse = await api.get("/notes/saved");
        const savedNotes = savedResponse.data?.notes || [];

        savedIds = new Set(
          savedNotes.map((note) => String(note.id))
        );
      } catch {
        // User may not be logged in. Public notes still work.
      }

      const formattedNotes = fetchedNotes.map((note) => ({
        id: String(note.id),
        name: note.title || note.filename || "Untitled note",
        size: Number(note.size) || 0,
        faculty: facultyName,
        department: departmentName,
        semester: note.semester || semester,
        fileUrl: note.file_url || note.file?.url || "",
        isSaved: savedIds.has(String(note.id)),
      }));

      setNotes(formattedNotes);
    } catch (err) {
      console.error("Failed to fetch notes:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to load notes. Please check your connection and try again."
      );
    } finally {
      setLoading(false);
    }
  }, [departmentId, semester, facultyName, departmentName]);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  const handleToggleSave = async (note) => {
    if (savingIds[note.id]) return;

    const shouldSave = !note.isSaved;

    setSavingIds((previous) => ({
      ...previous,
      [note.id]: true,
    }));

    try {
      if (shouldSave) {
        await api.post(`/notes/${note.id}/save`);
      } else {
        await api.delete(`/notes/${note.id}/save`);
      }

      setNotes((previous) =>
        previous.map((item) =>
          item.id === note.id
            ? { ...item, isSaved: shouldSave }
            : item
        )
      );
    } catch (err) {
      console.error("Failed to update saved note:", err);

      if (err.response?.status === 401) {
        window.alert("Please log in to save notes.");
      } else if (err.response?.status === 403) {
        window.alert("You don't have permission to save this note.");
      } else {
        window.alert(
          err.response?.data?.detail ||
            "Could not update the saved note. Please try again."
        );
      }
    } finally {
      setSavingIds((previous) => ({
        ...previous,
        [note.id]: false,
      }));
    }
  };

  return (
    <HomeLayout>
      <div className="min-h-screen bg-gray-50 px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <Link
            to={`/faculty/${facultyId}`}
            className="mb-6 inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition hover:bg-white hover:text-cyan-600"
          >
            <FiArrowLeft />
            Back to Departments
          </Link>

          {/* Page header */}
          <div className="mb-8 rounded-2xl border border-gray-100 bg-white p-6 shadow-inner shadow-gray-200 sm:p-8">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-600">
                  Notes Library
                </p>

                <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
                  Semester {semester} Notes
                </h1>

                <p className="mt-2 text-gray-500">
                  Browse, save, and access your study materials.
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-3 rounded-xl bg-cyan-50 p-4">
                <div className="rounded-lg bg-white p-3 text-cyan-600 shadow-sm">
                  <FiBookOpen size={24} />
                </div>

                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {loading ? "—" : notes.length}
                  </p>
                  <p className="text-sm text-gray-500">
                    Total Files
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-2 border-t border-gray-100 pt-5">
              <span className="rounded-full bg-cyan-50 px-3 py-1.5 text-sm font-medium text-cyan-700">
                {facultyName}
              </span>

              <span className="rounded-full bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700">
                {departmentName}
              </span>

              <span className="rounded-full bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700">
                Semester {semester}
              </span>
            </div>
          </div>

          {/* Section heading */}
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold text-gray-800">
                Available Files
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                {loading
                  ? "Loading study materials..."
                  : `${notes.length} files available`}
              </p>
            </div>

            <button
              type="button"
              onClick={fetchNotes}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-600 transition hover:border-cyan-300 hover:text-cyan-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <FiRefreshCw
                className={loading ? "animate-spin" : ""}
              />
              Refresh
            </button>
          </div>

          {/* Loading state */}
          {loading && (
            <div className="space-y-4" aria-live="polite">
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  className="animate-pulse rounded-2xl border border-gray-100 bg-white p-5 shadow-sm"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 shrink-0 rounded-xl bg-gray-200" />

                    <div className="flex-1 space-y-3">
                      <div className="h-4 w-2/3 rounded bg-gray-200" />
                      <div className="h-3 w-1/3 rounded bg-gray-100" />
                      <div className="h-3 w-1/2 rounded bg-gray-100" />
                    </div>

                    <div className="hidden h-9 w-24 rounded-lg bg-gray-100 sm:block" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error state */}
          {!loading && error && (
            <div
              role="alert"
              className="rounded-2xl border border-red-100 bg-white px-6 py-12 text-center"
            >
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-500">
                <FiAlertCircle size={26} />
              </div>

              <h3 className="text-lg font-semibold text-gray-800">
                Could not load notes
              </h3>

              <p className="mx-auto mt-2 max-w-lg text-sm text-gray-500">
                {error}
              </p>

              <button
                type="button"
                onClick={fetchNotes}
                className="mt-5 inline-flex items-center gap-2 rounded-lg bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700"
              >
                <FiRefreshCw />
                Try Again
              </button>
            </div>
          )}

          {/* Notes list */}
          {!loading && !error && notes.length > 0 && (
            <div className="space-y-4">
              {notes.map((file) => (
                <ShowingFiles
                  key={file.id}
                  id={file.id}
                  name={file.name}
                  size={file.size}
                  faculty={file.faculty}
                  department={file.department}
                  fileUrl={file.fileUrl}
                  isSaved={file.isSaved}
                  isSaving={Boolean(savingIds[file.id])}
                  onToggleSave={() => handleToggleSave(file)}
                />
              ))}
            </div>
          )}

          {/* Empty state */}
          {!loading && !error && notes.length === 0 && (
            <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-14 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-600">
                <FiFileText size={26} />
              </div>

              <h3 className="text-lg font-semibold text-gray-800">
                No notes available yet
              </h3>

              <p className="mt-2 text-sm text-gray-500">
                Study materials for this semester will appear here
                when they are uploaded.
              </p>
            </div>
          )}
        </div>
      </div>
    </HomeLayout>
  );
};

export default Notes;
