import type { BuyerBrief, MarketContext, PropertyEvent, PropertyGuidance, Relaxation, SourceItem, TraceStep } from "./types";

const API_URL = import.meta.env.VITE_AGENT_API_URL || "http://localhost:8002";

async function errorMessage(response: Response) {
  try {
    const body = await response.json() as { detail?: string };
    return body.detail || "Aizen could not complete this request.";
  } catch {
    return "Aizen could not complete this request.";
  }
}

export async function interpretBrief(query: string, threadId?: string, signal?: AbortSignal): Promise<BuyerBrief> {
  const response = await fetch(`${API_URL}/api/briefs/interpret`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, thread_id: threadId }),
    signal,
  });
  if (!response.ok) throw new Error(await errorMessage(response));
  return response.json() as Promise<BuyerBrief>;
}

type RunHandlers = {
  onStarted: (payload: { thread_id: string; snapshot_id: string }) => void;
  onStep: (step: TraceStep) => void;
  onProperties: (payload: PropertyEvent) => void;
  onSources: (sources: SourceItem[]) => void;
  onToken: (token: string) => void;
  onRelaxations: (items: Relaxation[]) => void;
  onGuidance: (guidance: PropertyGuidance) => void;
  onCompleted: (payload: Record<string, unknown>) => void;
};

export async function runBrief(brief: BuyerBrief, threadId: string, handlers: RunHandlers, signal?: AbortSignal) {
  const response = await fetch(`${API_URL}/api/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief, thread_id: threadId }),
    signal,
  });
  if (!response.ok || !response.body) throw new Error(await errorMessage(response));
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const dispatch = (block: string) => {
    const event = block.match(/^event: (.+)$/m)?.[1];
    const dataLine = block.match(/^data: (.+)$/m)?.[1];
    if (!event || !dataLine) return;
    const data = JSON.parse(dataLine) as Record<string, unknown>;
    if (event === "run_started") handlers.onStarted(data as { thread_id: string; snapshot_id: string });
    if (event === "agent_step") handlers.onStep(data as TraceStep);
    if (event === "properties") handlers.onProperties(data as unknown as PropertyEvent);
    if (event === "sources") handlers.onSources(data.items as SourceItem[]);
    if (event === "answer_token") handlers.onToken(data.token as string);
    if (event === "relaxation_options") handlers.onRelaxations(data.criteria as Relaxation[]);
    if (event === "guidance") handlers.onGuidance(data.guidance as PropertyGuidance);
    if (event === "run_completed") handlers.onCompleted(data);
    if (event === "run_failed") throw new Error(String(data.message || "Live run failed."));
  };
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    blocks.filter(Boolean).forEach(dispatch);
    if (done) break;
  }
  if (buffer.trim()) dispatch(buffer);
}

export async function compareAreas(areas: string[], propertyType?: string, beds?: number): Promise<MarketContext[]> {
  const response = await fetch(`${API_URL}/api/areas/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ areas, property_type: propertyType || null, beds: beds ?? null }),
  });
  if (!response.ok) throw new Error(await errorMessage(response));
  return (await response.json() as { areas: MarketContext[] }).areas;
}
