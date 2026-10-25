
import React from "react";
import {
  FiFileText,
  FiEye,
  FiDownload,
  FiHardDrive,
  FiBookmark,
  FiCheck,
  FiLoader,
} from "react-icons/fi";

const ShowingFiles = ({
  id,
  name = "Data Structures Notes.pdf",
  size = 0,
  faculty = "Engineering",
  department = "Computer Science & Engineering",
  fileUrl = "#",
  isSaved = false,
  isSaving = false,
  onToggleSave = () => {},
}) => {
  const formatSize = (bytes) => {
    if (bytes == null || bytes < 0) return "Unknown size";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    if (bytes < 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const handleView = () => {
    if (fileUrl && fileUrl !== "#") {
      window.open(fileUrl, "_blank", "noopener,noreferrer");
    }
  };

  const hasFileUrl = Boolean(fileUrl && fileUrl !== "#");

  return (
    <div
      data-note-id={id}
      className="group rounded-2xl border border-gray-100 bg-white p-4 shadow-inner shadow-gray-200 transition duration-200 hover:border-cyan-200 hover:shadow-lg hover:shadow-cyan-100 sm:p-5"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        {/* File information */}
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <div className="shrink-0 rounded-xl bg-cyan-50 p-3 text-cyan-600 transition group-hover:bg-cyan-100">
            <FiFileText size={25} />
          </div>

          <div className="min-w-0 flex-1">
            <h3
              title={name}
              className="break-words font-semibold text-gray-800"
            >
              {name}
            </h3>

            <div className="mt-2 flex items-center gap-1.5 text-sm text-gray-500">
              <FiHardDrive size={14} />
              <span>{formatSize(size)}</span>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <span className="rounded-full bg-cyan-50 px-2.5 py-1 text-xs font-medium text-cyan-700">
                {faculty}
              </span>

              <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">
                {department}
              </span>
            </div>
          </div>
        </div>

        {/* File actions */}
        <div className="flex shrink-0 flex-wrap gap-2 sm:flex-nowrap">
          {/* Save / Saved button */}
          <button
            type="button"
            onClick={onToggleSave}
            disabled={isSaving}
            aria-label={
              isSaving
                ? "Updating saved note"
                : isSaved
                  ? "Remove saved note"
                  : "Save note"
            }
            aria-pressed={isSaved}
            className={`inline-flex flex-1 items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-semibold transition disabled:cursor-wait disabled:opacity-70 sm:flex-none ${
              isSaved
                ? "border-cyan-200 bg-cyan-50 text-cyan-700 hover:bg-cyan-100"
                : "border-gray-200 bg-white text-gray-700 hover:border-cyan-200 hover:bg-cyan-50 hover:text-cyan-700"
            }`}
          >
            {isSaving ? (
              <FiLoader size={16} className="animate-spin" />
            ) : isSaved ? (
              <FiCheck size={16} />
            ) : (
              <FiBookmark size={16} />
            )}

            {isSaving
              ? "Saving..."
              : isSaved
                ? "Saved"
                : "Save"}
          </button>

          {/* View button */}
          <button
            type="button"
            onClick={handleView}
            disabled={!hasFileUrl}
            className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:border-cyan-200 hover:bg-cyan-50 hover:text-cyan-700 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none"
          >
            <FiEye size={16} />
            View
          </button>

          {/* Download button */}
          <a
            href={hasFileUrl ? fileUrl : undefined}
            download={name}
            target="_blank"
            rel="noopener noreferrer"
            aria-disabled={!hasFileUrl}
            onClick={(event) => {
              if (!hasFileUrl) {
                event.preventDefault();
              }
            }}
            className={`inline-flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition sm:flex-none ${
              hasFileUrl
                ? "bg-cyan-600 text-white hover:bg-cyan-700"
                : "cursor-not-allowed bg-gray-300 text-gray-500"
            }`}
          >
            <FiDownload size={16} />
            Download
          </a>
        </div>
      </div>
    </div>
  );
};

export default ShowingFiles;
