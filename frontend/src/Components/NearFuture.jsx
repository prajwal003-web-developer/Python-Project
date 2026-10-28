
import { FiClock, FiArrowLeft } from "react-icons/fi";
import { useNavigate } from "react-router-dom";

const ComingSoon = () => {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-[70vh] items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-2xl rounded-3xl border border-slate-100 bg-white px-6 py-12 text-center shadow-sm sm:px-12 sm:py-16">
        {/* Icon */}
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-cyan-50 text-cyan-700">
          <FiClock size={38} />
        </div>

        {/* Status */}
        <span className="mb-4 inline-flex rounded-full bg-cyan-50 px-4 py-2 text-xs font-bold uppercase tracking-widest text-cyan-700">
          Coming Soon
        </span>

        {/* Heading */}
        <h2 className="mt-3 text-3xl font-black tracking-tight text-slate-900 sm:text-4xl">
          Something Great Is on the Way!
        </h2>

        {/* Description */}
        <p className="mx-auto mt-5 max-w-md text-sm leading-7 text-slate-500 sm:text-base">
          We're working hard to bring you this feature. It will be
          available in the near future, helping make your learning
          experience with EduNotes even better.
        </p>

        {/* Thank you message */}
        <p className="mt-6 text-sm font-semibold text-cyan-700">
          Thank you for your patience 💙
        </p>

        {/* Back button */}
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mx-auto mt-8 inline-flex items-center gap-2 rounded-xl bg-cyan-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-cyan-700 focus:outline-none focus:ring-4 focus:ring-cyan-100"
        >
          <FiArrowLeft size={17} />
          Go Back
        </button>
      </div>
    </div>
  );
};

export default ComingSoon;
