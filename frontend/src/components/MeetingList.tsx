import type { Meeting } from "../api";

function formatRange(startsAt: string, endsAt: string) {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const dateFmt = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" });
  const timeFmt = new Intl.DateTimeFormat("en-GB", { timeStyle: "short" });
  return `${dateFmt.format(start)} · ${timeFmt.format(start)}–${timeFmt.format(end)}`;
}

export default function MeetingList({ meetings }: { meetings: Meeting[] }) {
  if (meetings.length === 0) {
    return <p className="text-sm text-gray-500">No meetings yet.</p>;
  }

  return (
    <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
      {meetings.map((m) => (
        <li key={m.id} className="flex items-center justify-between px-4 py-3">
          <div>
            <p className="font-medium text-gray-900">{m.title}</p>
            <p className="text-sm text-gray-500">{formatRange(m.starts_at, m.ends_at)}</p>
          </div>
          <span className="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-700">
            {m.attendee_count} attendee{m.attendee_count === 1 ? "" : "s"}
          </span>
        </li>
      ))}
    </ul>
  );
}
