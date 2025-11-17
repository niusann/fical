const TRACKED_PATHS = new Set(["/ipo.ics", "/earnings.ics", "/all.ics"]);

async function hashVisitorKey(value) {
  const data = new TextEncoder().encode(value);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export const onRequest = [
  async (context) => {
    const { request, env } = context;
    const url = new URL(request.url);

    if (!TRACKED_PATHS.has(url.pathname)) {
      return context.next();
    }

    if (env.ICS_ANALYTICS && typeof env.ICS_ANALYTICS.writeDataPoint === "function") {
      const ua = request.headers.get("user-agent") || "";
      const referer = request.headers.get("referer") || "";
      const ip = request.headers.get("cf-connecting-ip") || "";
      const country = (request.cf && request.cf.country) || "";
      const visitorKey = await hashVisitorKey(`${ip}|${ua}`);

      const logPromise = env.ICS_ANALYTICS.writeDataPoint({
        indexes: [visitorKey],
        blobs: [url.pathname, referer, ua.slice(0, 128), country],
        doubles: [],
      });

      const handle = Promise.resolve(logPromise).catch((err) => {
        console.error("ICS analytics write failed", err);
      });

      if (typeof context.waitUntil === "function") {
        context.waitUntil(handle);
      }
    }

    return context.next();
  },
];
