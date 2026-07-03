import { NextRequest, NextResponse } from "next/server"
const AGENT_URL = process.env.AGENT_URL || "http://127.0.0.1:8002"
export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams.toString()
  const url = `${AGENT_URL}/audit${params ? "?" + params : ""}`
  const res = await fetch(url)
  return NextResponse.json(await res.json(), { status: res.status })
}
