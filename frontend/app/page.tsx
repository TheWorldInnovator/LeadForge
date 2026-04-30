"use client";

import { useEffect, useState } from "react";
import LeadCard from "../components/leads-cards";
import ProgressPanel from "../components/progress-panel";
import { Sun, Moon } from "lucide-react";


type Lead = {
  name: string;
  rating: number;
  reviews: number;
  address: string;
  contact_number: string;
  website: string;
  opportunity: number;
  email_copy: string;
  display_reasoning: string;
};

export default function HomePage() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  const [niche, setNiche] = useState("");
  const [city, setCity] = useState("");

  const [leads, setLeads] = useState<Lead[]>([]);
  const [status, setStatus] = useState("idle");
  const [stage, setStage] = useState("Not started");
  const [progress, setProgress] = useState(0);
  const [scrapedCount, setScrapedCount] = useState(0);
  const [emailCount, setEmailCount] = useState(0);
  const [totalTarget, setTotalTarget] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") as "dark" | "light" | null;
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const startGeneration = async () => {
    if (!niche.trim() || !city.trim()) {
      setError("Please enter both niche and city.");
      return;
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/generate-leads", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          niche: niche.trim(),
          city: city.trim(),
        }),
      });

      const data = await res.json();

      setStatus(data.status || "running");
      setStage("Starting...");
      setProgress(0);
      setScrapedCount(0);
      setEmailCount(0);
      setTotalTarget(0);
      setError("");
      setLeads([]);
    } catch (err) {
      console.error(err);
      setError("Failed to start lead generation");
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/status");
      const data = await res.json();

      setStatus(data.status || "idle");
      setStage(data.stage || "Not started");
      setProgress(data.progress || 0);
      setScrapedCount(data.scraped_count || 0);
      setEmailCount(data.email_count || 0);
      setTotalTarget(data.total_target || 0);
      setError(data.error || "");

      if (data.status === "completed") {
        const leadsRes = await fetch("http://127.0.0.1:8000/leads");
        const leadsData = await leadsRes.json();
        setLeads(leadsData);
      }
    } catch (err) {
      console.error(err);
      setError("Failed to fetch status");
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const isDark = theme === "dark";

  return (
    <main
      className={`min-h-screen px-6 py-8 transition-colors duration-300 ${
        isDark ? "bg-black text-white" : "bg-gray-100 text-gray-900"
      }`}
    >
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="mb-6 text-4xl font-bold">Leads Dashboard</h1>

          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <input
              type="text"
              placeholder="Enter niche (e.g. dentists)"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              className={`w-full rounded-xl border px-4 py-2 placeholder-opacity-70 focus:outline-none focus:ring-2 focus:ring-cyan-400 md:w-1/3 ${
                isDark
                  ? "border-white/20 bg-white/10 text-white placeholder-white/50"
                  : "border-gray-300 bg-white text-gray-900 placeholder-gray-500"
              }`}
            />

            <input
              type="text"
              placeholder="Enter city (e.g. Dubai)"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className={`w-full rounded-xl border px-4 py-2 placeholder-opacity-70 focus:outline-none focus:ring-2 focus:ring-cyan-400 md:w-1/3 ${
                isDark
                  ? "border-white/20 bg-white/10 text-white placeholder-white/50"
                  : "border-gray-300 bg-white text-gray-900 placeholder-gray-500"
              }`}
            />

            <button
              onClick={startGeneration}
              disabled={status === "running"}
              className="rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-500 px-5 py-3 font-semibold text-white transition-all duration-300 hover:scale-105 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
            >
              {status === "running" ? "Generating..." : "Generate Leads for This Market"}
            </button>
          </div>
        </div>

        <button
        onClick={toggleTheme}
        className={`relative flex h-10 w-20 cursor-pointer items-center rounded-full p-1 transition-all duration-300 ${
          isDark ? "bg-gray-800" : "bg-gray-300"
        }`}
      >
        {/* Sliding Circle */}
        <div
          className={`absolute h-8 w-8 rounded-full shadow-md transition-all duration-300 ${
            isDark
              ? "translate-x-10 bg-black shadow-[0_0_20px_rgba(34,211,238,0.3)]"
              : "translate-x-0 bg-white"
          }`}
        />

        {/* Icons */}
        <div className="relative z-10 flex w-full items-center justify-between px-2">
          <Sun
          size={16}
          className={`transition-all duration-300 ${
            isDark ? "text-gray-500" : "text-yellow-400"
          }`}
        />
        <Moon
          size={16}
          className={`transition-all duration-300 ${
            isDark ? "text-cyan-400" : "text-gray-400"
          }`}
        />
        </div>
      </button>
            </div>

      {(status === "running" || status === "completed") && (
        <ProgressPanel
          status={status}
          stage={stage}
          progress={progress}
          scrapedCount={scrapedCount}
          emailCount={emailCount}
          totalTarget={totalTarget}
          isDark={isDark}
        />
      )}

      {error && (
        <div
          className={`mb-6 rounded-2xl border p-4 ${
            isDark
              ? "border-red-500/20 bg-red-500/10 text-red-300"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          {error}
        </div>
      )}

      {leads.length > 0 && (
  <div className="mt-6 mb-4 flex justify-start">
    <button
      onClick={exportToCSV}
      className="rounded-xl bg-green-600 px-6 py-3 font-semibold text-white transition hover:bg-green-700"
    >
      Export CSV
    </button>
  </div>
)}

      {status === "completed" && leads.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          {leads.map((lead, index) => (
            <LeadCard key={index} lead={lead} isDark={isDark} />
          ))}
        </div>
      ) : status === "running" ? (
        <p className={isDark ? "text-white/60" : "text-gray-600"}>
          Please wait while leads are being generated...
        </p>
      ) : (
        <p className={isDark ? "text-white/60" : "text-gray-600"}>
          Click Generate Leads to start.
        </p>
      )}
    </main>
  );
  function exportToCSV() {
  if (!leads || leads.length === 0) {
    alert("No leads to export.");
    return;
  }

  const headers = [
    "Name",
    "Rating",
    "Reviews",
    "Address",
    "Contact Number",
    "Website",
    "Opportunity",
    "Reasoning",
  ];

  const rows = leads.map((lead) => [
    lead.name,
    lead.rating,
    lead.reviews,
    lead.address,
    lead.contact_number,
    lead.website,
    lead.opportunity,
    lead.display_reasoning,
  ]);

  const csvContent = [
    headers.join(","),
    ...rows.map((row) =>
      row
        .map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`)
        .join(",")
    ),
  ].join("\n");

  const blob = new Blob([csvContent], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "leads.csv";
  link.click();

  URL.revokeObjectURL(url);
}
}
