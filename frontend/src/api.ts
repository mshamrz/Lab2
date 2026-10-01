const API_BASE = import.meta.env.VITE_API_URL || "";

export type Meeting = {
  id: number;
  title: string;
  starts_at: string;
  ends_at: string;
  attendee_count: number;
};

export type MeetingInput = {
  title: string;
  starts_at: string;
  ends_at: string;
  attendee_count: number;
};

export async function listMeetings(): Promise<Meeting[]> {
  const res = await fetch(`${API_BASE}/api/meetings`);
  if (!res.ok) {
    throw new Error(`Failed to load meetings: ${res.status}`);
  }
  return res.json();
}

export async function createMeeting(input: MeetingInput): Promise<Meeting> {
  const res = await fetch(`${API_BASE}/api/meetings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ? JSON.stringify(body.detail) : `Failed: ${res.status}`);
  }
  return res.json();
}
