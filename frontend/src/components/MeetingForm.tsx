import { useState } from "react";

import type { ActionItem, AgendaItem, MeetingInput } from "../api";
import { parseAgendaText } from "../api";

type Props = {
  onCreate: (input: MeetingInput) => Promise<void>;
  token?: string;
};

export default function MeetingForm({ onCreate, token }: Props) {
  // Form fields
  const [title, setTitle] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [attendeeCount, setAttendeeCount] = useState(1);
  const [agendaItems, setAgendaItems] = useState<AgendaItem[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [aiSuggestion, setAiSuggestion] = useState<unknown | null>(null);

  // Suggested flags (badge visible until user touches the field)
  const [suggestedFields, setSuggestedFields] = useState<Set<string>>(new Set());

  // Parser state
  const [pastedText, setPastedText] = useState("");
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  // Submit state
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function clearSuggested(field: string) {
    if (suggestedFields.has(field)) {
      const next = new Set(suggestedFields);
      next.delete(field);
      setSuggestedFields(next);
    }
  }

  async function handleParse() {
    if (!pastedText.trim()) return;
    if (!token) {
      setParseError("Please sign in first to use the AI agenda parser.");
      return;
    }
    setParseError(null);
    setIsParsing(true);
    const controller = new AbortController();
    setAbortController(controller);

    try {
      const res = await parseAgendaText(pastedText, token, controller.signal);
      const ag = res.agenda;
      const newSuggested = new Set<string>();

      if (ag.title) {
        setTitle(ag.title);
        newSuggested.add("title");
      }

      if (ag.starts_at) {
        try {
          const d = new Date(ag.starts_at);
          const pad = (n: number) => String(n).padStart(2, "0");
          const formatted = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
          setStartsAt(formatted);
          newSuggested.add("startsAt");

          if (ag.duration_minutes) {
            const endD = new Date(d.getTime() + ag.duration_minutes * 60000);
            const endFormatted = `${endD.getFullYear()}-${pad(endD.getMonth() + 1)}-${pad(endD.getDate())}T${pad(endD.getHours())}:${pad(endD.getMinutes())}`;
            setEndsAt(endFormatted);
            newSuggested.add("endsAt");
          }
        } catch {
          // ignore date parse error
        }
      }

      if (ag.items && ag.items.length > 0) {
        setAgendaItems(ag.items);
        newSuggested.add("agendaItems");
      }

      if (ag.action_items && ag.action_items.length > 0) {
        setActionItems(ag.action_items);
        newSuggested.add("actionItems");
      }

      setSuggestedFields(newSuggested);
      setAiSuggestion({
        agenda: ag,
        model: res.model,
        prompt_version: res.prompt_version,
      });
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setParseError("Parsing was cancelled.");
      } else {
        setParseError(err instanceof Error ? err.message : "Parsing failed");
      }
    } finally {
      setIsParsing(false);
      setAbortController(null);
    }
  }

  function handleCancelParse() {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setIsParsing(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onCreate({
        title,
        starts_at: new Date(startsAt).toISOString(),
        ends_at: new Date(endsAt).toISOString(),
        attendee_count: attendeeCount,
        agenda: agendaItems.length > 0 || actionItems.length > 0 ? {
          items: agendaItems,
          action_items: actionItems,
        } : undefined,
        ai_suggestion: aiSuggestion ?? undefined,
      });
      // reset form
      setTitle("");
      setStartsAt("");
      setEndsAt("");
      setAttendeeCount(1);
      setAgendaItems([]);
      setActionItems([]);
      setAiSuggestion(null);
      setSuggestedFields(new Set());
      setPastedText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Paste an agenda panel */}
      <div className="rounded-lg border border-purple-200 bg-purple-50/40 p-4">
        <label className="block text-sm font-semibold text-purple-950">
          Paste an agenda
        </label>
        <p className="mt-0.5 text-xs text-purple-700">
          Paste email, chat message or meeting notes. Claude will extract structured fields.
        </p>
        <textarea
          rows={3}
          value={pastedText}
          onChange={(e) => setPastedText(e.target.value)}
          placeholder="e.g. Пн 10:00, синк по прайсингу, 45 хв. 1) нові тарифи Pro — Олена..."
          className="mt-2 w-full rounded-md border border-purple-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
          disabled={isParsing}
        />

        <div className="mt-3 flex items-center justify-between">
          <button
            type="button"
            onClick={handleParse}
            disabled={isParsing || !pastedText.trim()}
            className="rounded-md bg-purple-700 px-3.5 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-purple-800 disabled:opacity-50"
          >
            {isParsing ? "Parsing…" : "Parse"}
          </button>

          {isParsing && (
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium text-purple-800 animate-pulse">
                Parsing agenda with Claude…
              </span>
              <button
                type="button"
                onClick={handleCancelParse}
                className="rounded border border-purple-300 bg-white px-2 py-1 text-xs font-medium text-purple-800 hover:bg-purple-100"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {parseError && (
          <p className="mt-2 text-xs font-medium text-red-600 bg-red-50 p-2 rounded border border-red-200">
            {parseError}
          </p>
        )}
      </div>

      {/* Main meeting form */}
      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="text-sm font-semibold text-gray-800">Add meeting</h2>
          {suggestedFields.size > 0 && (
            <span className="text-xs text-blue-600 font-medium">
              Fields marked with "suggested" were pre-filled by AI
            </span>
          )}
        </div>

        <div>
          <div className="flex items-center gap-2">
            <label className="block text-sm font-medium text-gray-700">Title</label>
            {suggestedFields.has("title") && (
              <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-700">
                suggested
              </span>
            )}
          </div>
          <input
            required
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              clearSuggested("title");
            }}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="flex items-center gap-2">
              <label className="block text-sm font-medium text-gray-700">Starts at</label>
              {suggestedFields.has("startsAt") && (
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-700">
                  suggested
                </span>
              )}
            </div>
            <input
              required
              type="datetime-local"
              value={startsAt}
              onChange={(e) => {
                setStartsAt(e.target.value);
                clearSuggested("startsAt");
              }}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <label className="block text-sm font-medium text-gray-700">Ends at</label>
              {suggestedFields.has("endsAt") && (
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-700">
                  suggested
                </span>
              )}
            </div>
            <input
              required
              type="datetime-local"
              value={endsAt}
              onChange={(e) => {
                setEndsAt(e.target.value);
                clearSuggested("endsAt");
              }}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Attendees</label>
          <input
            required
            type="number"
            min={0}
            value={attendeeCount}
            onChange={(e) => setAttendeeCount(Number(e.target.value))}
            className="mt-1 w-32 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
          />
        </div>

        {/* Structured Agenda items preview */}
        {agendaItems.length > 0 && (
          <div className="rounded-md border border-gray-200 bg-gray-50/70 p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold text-gray-700">Agenda topics</span>
              {suggestedFields.has("agendaItems") && (
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-700">
                  suggested
                </span>
              )}
            </div>
            <ul className="space-y-1.5 text-xs">
              {agendaItems.map((item, idx) => (
                <li key={idx} className="flex items-center justify-between text-gray-700 bg-white p-2 rounded border border-gray-100">
                  <span>
                    <strong className="text-gray-900">{item.topic}</strong>
                    {item.owner && <span className="text-gray-500"> — {item.owner}</span>}
                  </span>
                  {item.minutes && (
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-gray-600 font-mono">
                      {item.minutes}m
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action items preview */}
        {actionItems.length > 0 && (
          <div className="rounded-md border border-gray-200 bg-gray-50/70 p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold text-gray-700">Action items</span>
              {suggestedFields.has("actionItems") && (
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-700">
                  suggested
                </span>
              )}
            </div>
            <ul className="space-y-1.5 text-xs">
              {actionItems.map((act, idx) => (
                <li key={idx} className="flex items-center justify-between text-gray-700 bg-white p-2 rounded border border-gray-100">
                  <span>
                    <strong className="text-gray-900">{act.task}</strong>
                    {act.owner && <span className="text-gray-500"> ({act.owner})</span>}
                  </span>
                  {act.due && (
                    <span className="text-gray-500 font-mono">
                      due {act.due}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-gray-800 disabled:opacity-50"
        >
          {submitting ? "Saving…" : "Save meeting"}
        </button>
      </form>
    </div>
  );
}
