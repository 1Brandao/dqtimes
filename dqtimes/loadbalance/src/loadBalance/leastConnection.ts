import { createProxyServer } from "http-proxy";
import { IncomingMessage, ServerResponse } from "http";
import { Server } from "./server";

const proxy = createProxyServer({});

proxy.on("error", (err, req, res: any) => {
    console.error("[PROXY ERROR]", err);

    if (!res.headersSent) {
        res.writeHead(502);
    }
    res.end("Bad gateway");
});

export function leastConnections(
    servers: Server[],
    req: IncomingMessage,
    res: ServerResponse
) {
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
