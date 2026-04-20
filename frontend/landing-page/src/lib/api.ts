/**
 * API client for Kao Legal backend.
 */
import { fetchAuthSession } from "aws-amplify/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

async function getAuthToken(): Promise<string> {
  const session = await fetchAuthSession();
  const token = session.tokens?.idToken?.toString();
  if (!token) throw new Error("Not authenticated");
  return token;
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}

export interface MeetingSummaryRequest {
  transcript_or_notes: string;
  lawyer_name: string;
  client_code: string;
  client_name: string;
  matter_id: string;
  meeting_date: string;
  jurisdiction?: string;
  topic_tags?: string[];
}

export interface MeetingSummaryResponse {
  meeting_summary: string;
  agreed_actions: string[];
  deadlines: string[];
  open_questions: string[];
  email_subject: string;
  email_body_text: string;
  email_body_html: string;
  s3_summary_key: string;
  credits_consumed: number;
}

export async function createMeetingSummary(
  request: MeetingSummaryRequest
): Promise<MeetingSummaryResponse> {
  return apiRequest<MeetingSummaryResponse>("/api/v1/meeting/summary", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export interface PresignedUploadResponse {
  upload_url: string;
  s3_key: string;
  expires_in_seconds: number;
}

export async function getPresignedUploadUrl(
  filename: string,
  contentType: string,
  matterId: string
): Promise<PresignedUploadResponse> {
  return apiRequest<PresignedUploadResponse>("/api/v1/documents/upload-url", {
    method: "POST",
    body: JSON.stringify({ filename, content_type: contentType, matter_id: matterId }),
  });
}

export async function uploadToS3(file: File, presignedUrl: string): Promise<void> {
  const response = await fetch(presignedUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type },
  });

  if (!response.ok) {
    throw new Error(`S3 upload failed: HTTP ${response.status}`);
  }
}

export async function getCreditBalance(): Promise<{ credits: number }> {
  return apiRequest<{ credits: number }>("/api/v1/credits/");
}
