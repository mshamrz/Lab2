const API_BASE = import.meta.env.VITE_API_URL || "";
const PARSER_URL =
  import.meta.env.VITE_AGENDA_PARSER_URL ||
  "https://dwnx3qwwptlomoucjjtrac2eky0ydplh.lambda-url.us-east-1.on.aws/";

export type AgendaItem = {
  topic: string;
  owner: string | null;
  minutes: number | null;
};

export type ActionItem = {
  task: string;
  owner: string | null;
  due: string | null;
};

export type ParsedAgenda = {
  title: string | null;
  starts_at: string | null;
  duration_minutes: number | null;
  items: AgendaItem[];
  action_items: ActionItem[];
  language: string;
};

export type ParseAgendaResponse = {
  agenda: ParsedAgenda;
  model: string;
  prompt_version: string;
};

export type Meeting = {
  id: number;
  title: string;
  starts_at: string;
  ends_at: string;
  attendee_count: number;
  agenda?: unknown;
  ai_suggestion?: unknown;
};

export type MeetingInput = {
  title: string;
  starts_at: string;
  ends_at: string;
  attendee_count: number;
  agenda?: unknown;
  ai_suggestion?: unknown;
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

export async function parseAgendaText(
  text: string,
  token: string,
  signal?: AbortSignal,
): Promise<ParseAgendaResponse> {
  const today = new Date().toISOString().split("T")[0];
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Kyiv";

  let res: Response;
  try {
    res = await fetch(PARSER_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ text, today, tz }),
      signal,
    });
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw err;
    }
    throw new Error("Network failed. Please check your connection or fall back to typing by hand.");
  }

  if (!res.ok) {
    if (res.status === 401) {
      throw new Error("Authentication required. Please sign in to parse agendas.");
    }
    if (res.status === 413) {
      throw new Error("The text is too long (maximum 10,000 characters).");
    }
    if (res.status === 422) {
      throw new Error("The model could not find an agenda in the text.");
    }
    if (res.status === 429) {
      throw new Error("The service is busy (throttling), please try again in a minute.");
    }
    let errorDetail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data?.error) errorDetail = data.error;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return res.json();
}
