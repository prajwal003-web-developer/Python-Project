
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
    UserRound,
    Mail,
    Bookmark,
    FileText,
    Download,
    Eye,
    LogOut,
    Trash2,
    LoaderCircle,
    AlertCircle,
    X,
    ShieldCheck,
} from "lucide-react";
import api from "../Lib/api";
import useUserStore from "../Stores/useUserStore";
import AuthorizedLayout from "./Authorized/Layouts/AuthorizedLayout";



export default function Profile() {
    const navigate = useNavigate();

    const user = useUserStore((state) => state.user);
    const clearAuth = useUserStore((state) => state.clearAuth);

    const [savedNotes, setSavedNotes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [showLogoutDialog, setShowLogoutDialog] = useState(false);
    const [loggingOut, setLoggingOut] = useState(false);
    const [removingId, setRemovingId] = useState(null);

    // Support different user object formats.
    const fullName =
        user?.fullname ||
        user?.full_name ||
        user?.name ||
        "Student";

    const email =
        user?.gmail ||
        user?.email ||
        "No email available";

    const initials = fullName
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((word) => word[0].toUpperCase())
        .join("");

    // Fetch the user's saved notes.
    useEffect(() => {
        let active = true;

        const fetchSavedNotes = async () => {
            setLoading(true);
            setError("");

            try {
                // Change this endpoint if your backend uses a different route.
                const response = await api.get("/notes/saved");

                if (active) {
                    const data = response.data;

                    setSavedNotes(
                        Array.isArray(data)
                            ? data
                            : data?.notes || data?.saved_notes || []
                    );
                }
            } catch (err) {
                if (active) {
                    setError(
                        err.response?.data?.detail ||
                        "Couldn't load your saved notes. Please try again."
                    );
                }
            } finally {
                if (active) setLoading(false);
            }
        };

        fetchSavedNotes();

        return () => {
            active = false;
        };
    }, []);

    // Remove a note from the saved list.
    const handleRemoveSavedNote = async (noteId) => {
        if (!noteId) return;

        setRemovingId(noteId);

        try {
            // Change this endpoint to match your backend.
            await api.delete(`/notes/saved/${noteId}`);

            setSavedNotes((previous) =>
                previous.filter(
                    (note) => String(note._id || note.id) !== String(noteId)
                )
            );
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                "Couldn't remove this saved note."
            );
        } finally {
            setRemovingId(null);
        }
    };

    // Logout only after the user confirms.
    const handleLogout = async () => {
        setLoggingOut(true);

        try {
            await api.post("/auth/logout");
        } catch (err) {
            // A missing logout endpoint should not trap the user here.
            console.error("Logout request failed:", err);
        } finally {
            localStorage.removeItem("Token");
            clearAuth();
            setLoggingOut(false);
            setShowLogoutDialog(false);
            navigate("/login", { replace: true });
        }
    };

    return (
        <AuthorizedLayout>
            <div className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
                <div className="mx-auto max-w-5xl">
                    {/* Page heading */}
                    <div className="mb-8">
                        <p className="text-sm font-semibold uppercase tracking-wider text-cyan-700">
                            Your account
                        </p>
                        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
                            My Profile
                        </h1>
                        <p className="mt-2 text-slate-500">
                            Manage your account and access your saved study materials.
                        </p>
                    </div>

                    {/* Profile card */}
                    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
                        <div className="h-28 bg-gradient-to-r from-cyan-600 via-sky-500 to-blue-600" />

                        <div className="px-5 pb-6 sm:px-8">
                            <div className="-mt-12 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
                                <div className="flex items-end gap-4">
                                    <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-2xl border-4 border-white bg-cyan-50 text-2xl font-bold text-cyan-800 shadow-sm">
                                        {initials || <UserRound size={32} />}
                                    </div>

                                    <div className="pb-1">
                                        <h2 className="text-xl font-bold text-slate-900 sm:text-2xl">
                                            {fullName}
                                        </h2>
                                        <p className="mt-1 flex items-center gap-2 text-sm text-slate-500">
                                            <Mail size={15} />
                                            <span className="break-all">{email}</span>
                                        </p>
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    onClick={() => setShowLogoutDialog(true)}
                                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-200 px-4 py-2.5 text-sm font-semibold text-red-600 transition hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-200"
                                >
                                    <LogOut size={17} />
                                    Logout
                                </button>
                            </div>

                            <div className="mt-7 grid gap-4 border-t border-slate-100 pt-6 sm:grid-cols-2">
                                <div className="rounded-2xl bg-slate-50 p-4">
                                    <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-100 text-cyan-700">
                                        <UserRound size={20} />
                                    </div>
                                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                                        Full name
                                    </p>
                                    <p className="mt-1 break-words font-semibold text-slate-800">
                                        {fullName}
                                    </p>
                                </div>

                                <div className="rounded-2xl bg-slate-50 p-4">
                                    <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-700">
                                        <Mail size={20} />
                                    </div>
                                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                                        Email address
                                    </p>
                                    <p className="mt-1 break-all font-semibold text-slate-800">
                                        {email}
                                    </p>
                                </div>
                            </div>

                            <div className="mt-5 flex items-start gap-3 rounded-2xl border border-cyan-100 bg-cyan-50/70 p-4">
                                <ShieldCheck
                                    className="mt-0.5 shrink-0 text-cyan-700"
                                    size={20}
                                />
                                <div>
                                    <p className="font-semibold text-slate-800">
                                        Your learning space
                                    </p>
                                    <p className="mt-1 text-sm leading-6 text-slate-600">
                                        Browse academic notes, save useful resources, and return to
                                        them whenever you need to study.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Saved notes */}
                    <section className="mt-10">
                        <div className="mb-5 flex items-center justify-between gap-4">
                            <div>
                                <h2 className="flex items-center gap-2 text-xl font-bold text-slate-900 sm:text-2xl">
                                    <Bookmark className="text-cyan-700" size={23} />
                                    Saved Notes
                                </h2>
                                <p className="mt-1 text-sm text-slate-500">
                                    Your bookmarked study materials in one place.
                                </p>
                            </div>

                            {!loading && (
                                <span className="shrink-0 rounded-full bg-cyan-100 px-3 py-1 text-sm font-semibold text-cyan-800">
                                    {savedNotes.length} saved
                                </span>
                            )}
                        </div>

                        {loading ? (
                            <div className="flex flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white py-16">
                                <LoaderCircle className="animate-spin text-cyan-700" size={32} />
                                <p className="mt-3 text-sm text-slate-500">
                                    Loading your saved notes...
                                </p>
                            </div>
                        ) : error && savedNotes.length === 0 ? (
                            <div className="rounded-3xl border border-red-100 bg-white px-5 py-12 text-center">
                                <AlertCircle className="mx-auto text-red-500" size={32} />
                                <p className="mt-3 font-semibold text-slate-800">
                                    Something went wrong
                                </p>
                                <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
                                    {error}
                                </p>
                                <button
                                    type="button"
                                    onClick={() => window.location.reload()}
                                    className="mt-5 rounded-xl bg-cyan-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-cyan-800"
                                >
                                    Try again
                                </button>
                            </div>
                        ) : savedNotes.length === 0 ? (
                            <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-5 py-14 text-center">
                                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-700">
                                    <Bookmark size={30} />
                                </div>
                                <h3 className="mt-5 text-lg font-bold text-slate-900">
                                    No saved notes yet
                                </h3>
                                <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">
                                    When you find useful notes, save them to access them quickly
                                    from your profile.
                                </p>
                                <Link
                                    to="/"
                                    className="mt-6 inline-flex items-center justify-center rounded-xl bg-cyan-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-cyan-800"
                                >
                                    Explore notes
                                </Link>
                            </div>
                        ) : (
                            <div className="grid gap-4 md:grid-cols-2">
                                {savedNotes.map((note) => {
                                    const noteId = note._id || note.id;
                                    const title = note.title || note.name || "Untitled note";
                                    const description =
                                        note.description || "No description available.";
                                    const fileUrl =
                                        note.file_url || note.fileUrl || note.url || "";
                                    const fileName =
                                        note.file_name || note.filename || note.fileName || "";
                                    const fileType = (
                                        note.file_type ||
                                        note.fileType ||
                                        fileName.split(".").pop() ||
                                        "FILE"
                                    ).toUpperCase();

                                    return (
                                        <article
                                            key={noteId}
                                            className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-cyan-200 hover:shadow-md"
                                        >
                                            <div className="flex items-start gap-4">
                                                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700">
                                                    <FileText size={24} />
                                                </div>

                                                <div className="min-w-0 flex-1">
                                                    <h3 className="line-clamp-2 font-bold text-slate-900">
                                                        {title}
                                                    </h3>
                                                    <p className="mt-1 line-clamp-2 text-sm leading-5 text-slate-500">
                                                        {description}
                                                    </p>
                                                    <span className="mt-3 inline-block rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
                                                        {fileType}
                                                    </span>
                                                </div>

                                                <button
                                                    type="button"
                                                    title="Remove saved note"
                                                    disabled={removingId === noteId}
                                                    onClick={() => handleRemoveSavedNote(noteId)}
                                                    className="rounded-lg p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                                                >
                                                    {removingId === noteId ? (
                                                        <LoaderCircle size={18} className="animate-spin" />
                                                    ) : (
                                                        <Trash2 size={18} />
                                                    )}
                                                </button>
                                            </div>

                                            <div className="mt-5 flex flex-wrap gap-3 border-t border-slate-100 pt-4">
                                                {fileUrl ? (
                                                    <>
                                                        <a
                                                            href={fileUrl}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="inline-flex items-center gap-2 rounded-lg bg-cyan-700 px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-cyan-800"
                                                        >
                                                            <Eye size={16} />
                                                            View
                                                        </a>

                                                        <a
                                                            href={fileUrl}
                                                            download={fileName || title}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3.5 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                                                        >
                                                            <Download size={16} />
                                                            Download
                                                        </a>
                                                    </>
                                                ) : (
                                                    <p className="text-sm text-slate-400">
                                                        File link unavailable
                                                    </p>
                                                )}
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        )}
                    </section>
                </div>

                {/* Logout confirmation dialog */}
                {showLogoutDialog && (
                    <div
                        className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm"
                        onClick={(event) => {
                            if (event.target === event.currentTarget && !loggingOut) {
                                setShowLogoutDialog(false);
                            }
                        }}
                    >
                        <div
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="logout-dialog-title"
                            className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl sm:p-7"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-50 text-red-600">
                                    <LogOut size={23} />
                                </div>

                                <button
                                    type="button"
                                    disabled={loggingOut}
                                    onClick={() => setShowLogoutDialog(false)}
                                    aria-label="Close dialog"
                                    className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            <h2
                                id="logout-dialog-title"
                                className="mt-5 text-xl font-bold text-slate-900"
                            >
                                Log out of your account?
                            </h2>
                            <p className="mt-2 text-sm leading-6 text-slate-500">
                                Are you sure you want to log out? You'll need to log in again
                                to access your account and saved notes.
                            </p>

                            <div className="mt-7 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                                <button
                                    type="button"
                                    disabled={loggingOut}
                                    onClick={() => setShowLogoutDialog(false)}
                                    className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                                >
                                    Cancel
                                </button>

                                <button
                                    type="button"
                                    disabled={loggingOut}
                                    onClick={handleLogout}
                                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-red-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    {loggingOut ? (
                                        <>
                                            <LoaderCircle size={17} className="animate-spin" />
                                            Logging out...
                                        </>
                                    ) : (
                                        <>
                                            <LogOut size={17} />
                                            Yes, log out
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </AuthorizedLayout>
    );
}
