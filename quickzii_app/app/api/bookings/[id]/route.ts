import { NextRequest, NextResponse } from "next/server"

const MT_URL = process.env.MOTIONTOOLS_URL || "http://127.0.0.1:8001"

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const res = await fetch(`${MT_URL}/bookings/${params.id}`)
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}
