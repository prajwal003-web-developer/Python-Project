import React from "react";
import { FiBookOpen } from "react-icons/fi";

const Loading = ({ message = "Loading your study resources..." }) => {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
      <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-cyan-50">
        <FiBookOpen size={34} className="text-cyan-600" />

        <span className="absolute -right-1 -top-1 h-5 w-5 animate-ping rounded-full bg-cyan-400 opacity-50" />
        <span className="absolute -right-1 -top-1 h-5 w-5 rounded-full border-4 border-white bg-cyan-600" />
      </div>

      <h2 className="mt-6 text-lg font-bold text-gray-800">
        ADTU Notes
      </h2>

      <p className="mt-2 text-center text-sm text-gray-500">{message}</p>

      <div className="mt-5 h-1.5 w-48 overflow-hidden rounded-full bg-gray-100">
        <div className="h-full w-1/2 animate-pulse rounded-full bg-cyan-600" />
      </div>
    </div>
  );
};

export default Loading;