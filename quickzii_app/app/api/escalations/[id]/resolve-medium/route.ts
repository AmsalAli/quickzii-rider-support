import { NextRequest, NextResponse } from "next/server"
const AGENT_URL = process.env.AGENT_URL || "http://127.0.0.1:8002"
export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.json()
  const res = await fetch(`${AGENT_URL}/escalations/${params.id}/resolve-medium`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  return NextResponse.json(await res.json(), { status: res.status })
}
