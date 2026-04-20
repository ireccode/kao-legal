"use client";

import { useState } from "react";
import { DocumentUpload } from "@/components/DocumentUpload";

export default function DocumentsPage() {
  const [matterId, setMatterId] = useState("");
  const [clientCode, setClientCode] = useState("");
  const [s3Keys, setS3Keys] = useState<string[]>([]);
  const [result, setResult] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRunIntake = async () => {
    if (!s3Keys.length || !matterId || !clientCode) return;
    setError("");
    setLoading(true);

    try {
      const { fetchAuthSession } = await import("aws-amplify/auth");
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      const response = await fetch("/api/v1/documents/intake", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          s3_keys: s3Keys,
          client_code: clientCode,
          matter_id: matterId,
          document_group_id: `${matterId}-${Date.now()}`,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail ?? "Intake failed");
      }

      setResult(await response.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">Document Intake</h1>

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded">{error}</div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <input
          type="text"
          value={matterId}
          onChange={(e) => setMatterId(e.target.value)}
          placeholder="Matter ID"
          className="px-4 py-2 border rounded-lg"
        />
        <input
          type="text"
          value={clientCode}
          onChange={(e) => setClientCode(e.target.value)}
          placeholder="Client Code"
          className="px-4 py-2 border rounded-lg"
        />
      </div>

      {matterId && (
        <DocumentUpload matterId={matterId} onUploaded={setS3Keys} />
      )}

      {s3Keys.length > 0 && !result && (
        <>
          <p className="text-sm text-gray-600">
            Cost: {s3Keys.length * 5} credits ({s3Keys.length} documents)
          </p>
          <button
            onClick={handleRunIntake}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg disabled:opacity-50"
          >
            {loading ? "Analysing..." : "Run Document Intake"}
          </button>
        </>
      )}

      {result && (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
