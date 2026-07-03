import { NextResponse } from "next/server"
const AGENT_URL = process.env.AGENT_URL || "http://127.0.0.1:8002"
export async function GET() {
  const res = await fetch(`${AGENT_URL}/escalations/medium`)
  return NextResponse.json(await res.json(), { status: res.status })
}
