"use client";

import { useState } from "react";
import { createMeetingSummary, type MeetingSummaryResponse } from "@/lib/api";

export function MeetingSummaryForm() {
  const [transcript, setTranscript] = useState("");
  const [lawyerName, setLawyerName] = useState("");
  const [clientCode, setClientCode] = useState("");
  const [clientName, setClientName] = useState("");
  const [matterId, setMatterId] = useState("");
  const [meetingDate, setMeetingDate] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<MeetingSummaryResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await createMeetingSummary({
        transcript_or_notes: transcript,
        lawyer_name: lawyerName,
        client_code: clientCode,
        client_name: clientName,
        matter_id: matterId,
        meeting_date: new Date(meetingDate).toISOString(),
        jurisdiction,
      });
      setResult(response);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-6">Meeting Summary</h1>

      {!result ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 text-red-700 rounded">{error}</div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              value={lawyerName}
              onChange={(e) => setLawyerName(e.target.value)}
              placeholder="Lawyer Name"
              required
              className="px-4 py-2 border rounded-lg"
            />
            <input
              type="text"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              placeholder="Client Name"
              required
              className="px-4 py-2 border rounded-lg"
            />
            <input
              type="text"
              value={clientCode}
              onChange={(e) => setClientCode(e.target.value)}
              placeholder="Client Code (e.g. CLI001)"
              required
              className="px-4 py-2 border rounded-lg"
            />
            <input
              type="text"
              value={matterId}
              onChange={(e) => setMatterId(e.target.value)}
              placeholder="Matter ID"
              required
              className="px-4 py-2 border rounded-lg"
            />
            <input
              type="datetime-local"
              value={meetingDate}
              onChange={(e) => setMeetingDate(e.target.value)}
              required
              className="px-4 py-2 border rounded-lg"
            />
            <input
              type="text"
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              placeholder="Jurisdiction (optional)"
              className="px-4 py-2 border rounded-lg"
            />
          </div>

          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Paste meeting transcript or notes here..."
            required
            rows={12}
            className="w-full px-4 py-2 border rounded-lg font-mono text-sm"
          />

          <p className="text-sm text-gray-500">Cost: 10 credits</p>

          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg disabled:opacity-50"
          >
            {loading ? "Generating summary..." : "Generate Summary"}
          </button>
        </form>
      ) : (
        <div className="space-y-6">
          <div className="p-4 bg-green-50 rounded-lg">
            <h2 className="font-semibold mb-2">Meeting Summary</h2>
            <p>{result.meeting_summary}</p>
          </div>

          <div>
            <h2 className="font-semibold mb-2">Agreed Actions</h2>
            <ul className="list-disc pl-6 space-y-1">
              {result.agreed_actions.map((action, i) => (
                <li key={i}>{action}</li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="font-semibold mb-2">Key Deadlines</h2>
            <ul className="list-disc pl-6 space-y-1">
              {result.deadlines.map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <h2 className="font-semibold mb-2">Email Draft</h2>
            <p className="text-sm text-gray-600 mb-2">
              Subject: {result.email_subject}
            </p>
            <pre className="text-sm whitespace-pre-wrap">{result.email_body_text}</pre>
          </div>

          <button
            onClick={() => setResult(null)}
            className="px-4 py-2 border rounded-lg"
          >
            New Summary
          </button>
        </div>
      )}
    </div>
  );
}
