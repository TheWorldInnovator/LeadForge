type ProgressPanelProps = {
  status: string;
  stage: string;
  progress: number;
  scrapedCount: number;
  emailCount: number;
  totalTarget: number;
  isDark: boolean;
};

export default function ProgressPanel({
  status,
  stage,
  progress,
  scrapedCount,
  emailCount,
  totalTarget,
  isDark,
}: ProgressPanelProps) {
  return (
    <div
      className={`mb-8 overflow-hidden rounded-3xl border p-6 shadow-2xl backdrop-blur-xl ${
        isDark
          ? "border-white/10 bg-white/5"
          : "border-gray-200 bg-white"
      }`}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className={`text-2xl font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>
            Lead Generation Progress
          </h2>
          <p className={`mt-1 text-sm ${isDark ? "text-white/60" : "text-gray-500"}`}>
            {stage}
          </p>
        </div>

        <div
          className={`rounded-full px-4 py-2 text-sm font-semibold ${
            isDark
              ? "border border-cyan-400/20 bg-cyan-400/10 text-cyan-300"
              : "border border-cyan-200 bg-cyan-50 text-cyan-700"
          }`}
        >
          {progress}%
        </div>
      </div>

      <div className={`relative h-5 overflow-hidden rounded-full ${isDark ? "bg-white/10" : "bg-gray-200"}`}>
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-blue-500 via-cyan-400 to-blue-500 transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
        <div className="absolute inset-0 animate-pulse bg-white/5" />
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div
          className={`rounded-2xl border p-4 ${
            isDark
              ? "border-white/10 bg-black/20"
              : "border-gray-200 bg-gray-50"
          }`}
        >
          <p className={`text-sm ${isDark ? "text-white/50" : "text-gray-500"}`}>Status</p>
          <p className={`mt-1 text-lg font-semibold capitalize ${isDark ? "text-white" : "text-gray-900"}`}>
            {status}
          </p>
        </div>

        <div
          className={`rounded-2xl border p-4 ${
            isDark
              ? "border-white/10 bg-black/20"
              : "border-gray-200 bg-gray-50"
          }`}
        >
          <p className={`text-sm ${isDark ? "text-white/50" : "text-gray-500"}`}>
            Qualified Leads Generated
          </p>
          <p className={`mt-1 text-lg font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>
            {scrapedCount}
          </p>
        </div>

        <div
          className={`rounded-2xl border p-4 ${
            isDark
              ? "border-white/10 bg-black/20"
              : "border-gray-200 bg-gray-50"
          }`}
        >
          <p className={`text-sm ${isDark ? "text-white/50" : "text-gray-500"}`}>
            Emails Generated
          </p>
          <p className={`mt-1 text-lg font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>
            {emailCount}
            {totalTarget > 0 ? ` / ${totalTarget}` : ""}
          </p>
        </div>
      </div>
    </div>
  );
}