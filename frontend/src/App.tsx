import { useEffect, useState } from "react";

import { createMeeting, listMeetings } from "./api";
import type { Meeting, MeetingInput } from "./api";
import MeetingForm from "./components/MeetingForm";
import MeetingList from "./components/MeetingList";

export default function App() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function refresh() {
    try {
      setMeetings(await listMeetings());
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Could not load meetings");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate(input: MeetingInput) {
    await createMeeting(input);
    await refresh();
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Spry — Meetings</h1>
      <div className="space-y-6">
        <MeetingForm onCreate={handleCreate} />
        {loading && <p className="text-sm text-gray-500">Loading…</p>}
        {loadError && <p className="text-sm text-red-600">{loadError}</p>}
        {!loading && !loadError && <MeetingList meetings={meetings} />}
      </div>
    </div>
  );
}
