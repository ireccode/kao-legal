"use client";

import { useState } from "react";
import { getPresignedUploadUrl, uploadToS3 } from "@/lib/api";

interface UploadedFile {
  filename: string;
  s3_key: string;
}

export function DocumentUpload({
  matterId,
  onUploaded,
}: {
  matterId: string;
  onUploaded: (keys: string[]) => void;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploaded, setUploaded] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (!files.length || !matterId) return;
    setError("");
    setUploading(true);

    const newUploads: UploadedFile[] = [];

    try {
      for (const file of files) {
        const { upload_url, s3_key } = await getPresignedUploadUrl(
          file.name,
          file.type,
          matterId
        );
        await uploadToS3(file, upload_url);
        newUploads.push({ filename: file.name, s3_key });
      }

      const allUploaded = [...uploaded, ...newUploads];
      setUploaded(allUploaded);
      setFiles([]);
      onUploaded(allUploaded.map((u) => u.s3_key));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded">{error}</div>
      )}

      <input
        type="file"
        multiple
        accept=".pdf,.docx,.txt"
        onChange={handleFilesChange}
        className="block w-full text-sm text-gray-600"
      />

      {files.length > 0 && (
        <div className="text-sm text-gray-600">
          {files.length} file(s) selected
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={uploading || !files.length}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
      >
        {uploading ? "Uploading..." : "Upload"}
      </button>

      {uploaded.length > 0 && (
        <div>
          <p className="text-sm font-medium">Uploaded:</p>
          <ul className="text-sm text-gray-600 list-disc pl-4">
            {uploaded.map((f, i) => (
              <li key={i}>{f.filename}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
