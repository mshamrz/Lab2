import { useEffect, useState } from "react";
import { useAuth } from "react-oidc-context";

import { cognitoSignOutUrl } from "./auth";

import { createMeeting, listMeetings } from "./api";
import type { Meeting, MeetingInput } from "./api";
import MeetingForm from "./components/MeetingForm";
import MeetingList from "./components/MeetingList";

export default function App() {
  const auth = useAuth();
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
            <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Spry — Meetings</h1>
        {auth.isAuthenticated ? (
          <div className="flex items-center gap-3 text-sm">
            <span className="text-gray-700">{auth.user?.profile.email}</span>
            <button
              onClick={() => {
                auth.removeUser();
                window.location.href = cognitoSignOutUrl();
              }}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-gray-700 hover:bg-gray-50"
            >
              Sign out
            </button>
          </div>
        ) : (
          <button
            onClick={() => auth.signinRedirect()}
            className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white"
          >
            Sign in
          </button>
        )}
      </div>
      <div className="space-y-6">
        <MeetingForm onCreate={handleCreate} />
        {loading && <p className="text-sm text-gray-500">Loading…</p>}
        {loadError && <p className="text-sm text-red-600">{loadError}</p>}
        {!loading && !loadError && <MeetingList meetings={meetings} />}
      </div>
    </div>
  );
}
