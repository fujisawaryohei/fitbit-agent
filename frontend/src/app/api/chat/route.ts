import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) throw new Error("BACKEND_URL is not set");

  const backendResponse = await fetch(`${backendUrl}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: request.headers.get("cookie") ?? "",
    },
    body: JSON.stringify(body),
  });

  if (!backendResponse.ok) {
    const error = await backendResponse
      .json()
      .catch(() => ({ detail: "エラーが発生しました" }));
    return new Response(JSON.stringify(error), {
      status: backendResponse.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(backendResponse.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
