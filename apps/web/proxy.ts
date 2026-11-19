import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function proxy(request: NextRequest) {

    const session = request.cookies.get("session")?.value;

    if (!session) {
        return NextResponse.redirect(new URL("/login", request.url))
    }

    try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
            method: "GET",
            headers: {
                Cookie: `session=${session}`
            },
            cache: "no-store"
        });


        if (response.status == 401 || response.status == 403) {
            return NextResponse.redirect(new URL("/login", request.url));
        }

        if (!response.ok) {
            return new NextResponse("Authentication service unavailable", {
                status: 503,
            });
        }

        return NextResponse.next();
    }
    catch (error) {
        console.error("Session validation failed:", error);

        return new NextResponse("Authentication service unavailable", {
            status: 503,
        });
    }
}


export const config = {
    matcher: [
        "/((?!login|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
    ],
};