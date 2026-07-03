import { NextRequest, NextResponse } from "next/server"

const AGENT_URL = process.env.AGENT_URL || "http://127.0.0.1:8002"

export async function POST(req: NextRequest) {
  const body = await req.json()
  const res = await fetch(`${AGENT_URL}/converse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}
