import { createProxyServer } from "http-proxy";
import { IncomingMessage, ServerResponse } from "http";
import { Server } from "./server";

const proxy = createProxyServer({});

// Handle proxy responses to add CORS headers
proxy.on("proxyRes", (proxyRes, req, res) => {
    // Add CORS headers to all responses
    proxyRes.headers["Access-Control-Allow-Origin"] = "*";
    proxyRes.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS";
    proxyRes.headers["Access-Control-Allow-Headers"] = "*";
    proxyRes.headers["Access-Control-Expose-Headers"] = "*";
});

proxy.on("error", (err, req, res: any) => {
    console.error("[PROXY ERROR]", err);

    if (!res.headersSent) {
        res.writeHead(502, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        });
    }
    res.end("Bad gateway");
});

export function leastConnections(
    servers: Server[],
    req: IncomingMessage,
    res: ServerResponse
) {
    // Handle CORS preflight requests
    if (req.method === "OPTIONS") {
        res.writeHead(200, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        });
        res.end();
        return;
    }

    servers.sort((a, b) => a.connections - b.connections);

    const target = servers[0];
    if (!target) throw new TypeError("0 Servers found");

    target.connections++;

    proxy.web(req, res, {
        target: target.url,
        proxyTimeout: Number(process.env.PROXY_TIMEOUT || 30000),
    });

    const decrement = () => {
        target.connections = Math.max(0, target.connections - 1);
    };

    res.on("finish", decrement);

    res.on("close", decrement);
}
