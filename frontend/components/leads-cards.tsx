"use client";

import { useState } from "react";

type Lead = {
  name: string;
  rating: number;
  reviews: number;
  address: string;
  contact_number: string;
  website: string;
  opportunity: number;
  email_copy: string;
  display_reasoning: string
};

export default function LeadCard({
  lead,
  isDark,
}: {
  lead: Lead;
  isDark: boolean;
}) {
  const [showOutreach, setShowOutreach] = useState(false);
  const [copied, setCopied] = useState(false);
  const [email, setEmail] = useState("");
  const [loadingEmail, setLoadingEmail] = useState(false);



  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(email || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch (error) {
      console.error("Copy failed:", error);
    }
  };
  const handleGenerateEmail = async () => {
  setShowOutreach(true);
  setLoadingEmail(true);

  try {
    const API_URL = process.env.NEXT_PUBLIC_API_URL;

    const res = await fetch(`${API_URL}/generate-email`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(lead),
    });

    const data = await res.json();
    setEmail(data.email || "No outreach email generated.");
  } catch (error) {
    console.error("Email generation failed:", error);
    setEmail("Failed to generate email.");
  } finally {
    setLoadingEmail(false);
  }
};

  return (
    <div
      className={`group rounded-2xl border p-6 shadow-lg transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${
        isDark
          ? "border-white/20 bg-black text-white"
          : "border-gray-200 bg-white text-gray-900"
      }`}
    >
      <h2 className="mb-4 text-2xl font-bold leading-tight">{lead.name}</h2>

      <div className="space-y-2 text-lg">
        <p>Rating: {lead.rating}</p>
        <p>Reviews: {lead.reviews}</p>
        <p>Address: {lead.address}</p>
        <p>Contact: {lead.contact_number}</p>
        <p>
          Opportunity:{" "}
          <span className="font-bold text-red-500">{lead.opportunity}</span>
        </p>
        <p
          className={`text-sm leading 6 ${
            isDark ? "text-white/65" : "text-gray-600"
          }`}
          >
            {lead.display_reasoning}
          </p>
        <a
          href={lead.website}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block text-blue-500 underline transition hover:text-blue-400"
        >
          Website
        </a>
      </div>

      <div className="mt-5">
        <button
          onClick={email ? () => setShowOutreach((prev) => !prev) : handleGenerateEmail}
          className="rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 px-4 py-2 font-semibold text-white transition-all duration-300 hover:scale-105 hover:shadow-lg active:scale-95"
        >
          {loadingEmail
           ? "Generating..." 
           : showOutreach
           ? "Hide Outreach..."
           : email
           ? "Show Outreach..."
           : "Generate Outreach"
          }
        </button>
      </div>

      <div
        className={`grid transition-all duration-500 ease-in-out ${
          showOutreach ? "mt-5 grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        }`}
      >
        <div className="overflow-hidden">
          <div
            className={`relative rounded-2xl border p-4 backdrop-blur-sm ${
              isDark
                ? "border-cyan-400/30 bg-white/5"
                : "border-cyan-200 bg-cyan-50"
            }`}
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className={`text-lg font-semibold ${isDark ? "text-cyan-300" : "text-cyan-700"}`}>
                Outreach Email
              </h3>

              <button
                onClick={handleCopy}
                className={`rounded-full border px-3 py-2 text-sm transition-all duration-300 ${
                  copied
                    ? "border-green-400 bg-green-500/20 text-green-300 scale-110"
                    : isDark
                    ? "border-white/20 bg-white/10 text-white hover:scale-110 hover:bg-white/20"
                    : "border-gray-300 bg-white text-gray-700 hover:scale-110 hover:bg-gray-100"
                }`}
                title="Copy to clipboard"
              >
                {copied ? "Copied!" : "📋"}
              </button>
            </div>

            <pre
              className={`whitespace-pre-wrap break-words font-sans text-sm leading-7 ${
                isDark ? "text-white/90" : "text-gray-800"
              }`}
            >
              {loadingEmail ? "Generating outreach email..." : email || "No outreach email available."}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

