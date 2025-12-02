import { createServer } from "http"
import { Server } from "./loadBalance/server";
import { leastConnections } from "./loadBalance/leastConnection";
import dotenv from "dotenv";
dotenv.config();

const port = Number(process.env.LB_PORT || 8000);
const clientServers: Server[] = process.env.CLIENT_SERVERS!
  .split(",")
  .map(url => ({ connections: 0, url }));

// Configurable environment values
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
const CORS_PATHS = (process.env.CORS_PATHS || "/api,/app").split(",").map(s => s.trim()).filter(Boolean);
const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 60_000);
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX || 60);
const UPLOAD_PATHS = (process.env.UPLOAD_PATHS || "/upload").split(",").map(s => s.trim()).filter(Boolean);
const UPLOAD_MAX_BYTES = Number(process.env.UPLOAD_MAX_BYTES || 10 * 1024 * 1024); // 10 MB default for uploads
const UPLOAD_TIMEOUT_MS = Number(process.env.UPLOAD_TIMEOUT_MS || 120_000); // 2 minutes
const DEFAULT_MAX_BYTES = Number(process.env.DEFAULT_MAX_BYTES || 1 * 1024 * 1024); // 1 MB default
const DEFAULT_TIMEOUT_MS = Number(process.env.DEFAULT_TIMEOUT_MS || 30_000); // 30s default

// Simple in-memory rate limiter: Map<ip, Map<route, {count, resetAt}>>
const rateLimits = new Map<string, Map<string, { count: number; resetAt: number }>>();

function getClientIp(req: any): string {
    const headers = req.headers ?? {};
    const xff = headers['x-forwarded-for'];
    
    if (xff && typeof xff === 'string') return String(xff.split(',')[0]).trim();
    return req.socket && (req.socket.remoteAddress || '') || '';
}

function pathMatchesList(path: string, list: string[]) {
    return list.some(p => p && (p === path || path.startsWith(p)));
}

const loadBalance = createServer((req: any, res: any) => {
    try {
        // Security headers
        res.setHeader('X-Frame-Options', 'DENY');
        res.setHeader('X-Content-Type-Options', 'nosniff');
        res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

        const origin = (req.headers && req.headers.origin) || '';
        const path = (req.url || '/').split('?')[0];

        // CORS handling for configured paths
        const isCorsPath = pathMatchesList(path, CORS_PATHS);
        const originAllowed = ALLOWED_ORIGINS.length === 0 || ALLOWED_ORIGINS.includes(origin);

        if (isCorsPath && origin) {
            if (originAllowed) {
                res.setHeader('Access-Control-Allow-Origin', origin);
                res.setHeader('Access-Control-Allow-Credentials', 'true');
                res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
                res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
            }
            if (req.method === 'OPTIONS') {
                res.writeHead(originAllowed ? 204 : 403);
                return res.end();
            }
        }

        // Rate limiting
        const ip = getClientIp(req) || 'unknown';
        const routeKey = `${req.method || 'GET'} ${path}`;
        const now = Date.now();

        if (!rateLimits.has(ip)) rateLimits.set(ip, new Map());
        const ipMap = rateLimits.get(ip)!;
        const entry = ipMap.get(routeKey) || { count: 0, resetAt: now + RATE_LIMIT_WINDOW_MS };

        if (now > entry.resetAt) {
            entry.count = 0;
            entry.resetAt = now + RATE_LIMIT_WINDOW_MS;
        }

        entry.count++;
        ipMap.set(routeKey, entry);

        if (entry.count > RATE_LIMIT_MAX) {
            res.writeHead(429, { 'Content-Type': 'text/plain' });
            return res.end('Too many requests');
        }

        // Upload exceptions and size/time limits
        const isUploadPath = pathMatchesList(path, UPLOAD_PATHS);
        const contentType = (req.headers && req.headers['content-type'] || '').toString();
        const isCsvOrTxt = /text\/(csv|plain)/i.test(contentType) || /\.(csv|txt)$/i.test(path);
        const isUpload = isUploadPath || isCsvOrTxt;

        const allowedMaxBytes = isUpload ? UPLOAD_MAX_BYTES : DEFAULT_MAX_BYTES;
        const allowedTimeout = isUpload ? UPLOAD_TIMEOUT_MS : DEFAULT_TIMEOUT_MS;

        const clHeader = req.headers && req.headers['content-length'];
        const contentLength = clHeader ? parseInt(clHeader as string, 10) : NaN;
        if (!Number.isNaN(contentLength) && contentLength > allowedMaxBytes) {
            res.writeHead(413, { 'Content-Type': 'text/plain' });
            return res.end('Payload too large');
        }

        // For chunked requests without content-length we track bytes to enforce size limit
        let receivedBytes = 0;
        let exceeded = false;
        if (req.method === 'POST' || req.method === 'PUT') {
            const onData = (chunk: any) => {
                receivedBytes += chunk.length || 0;
                if (receivedBytes > allowedMaxBytes && !exceeded) {
                    exceeded = true;
                    try {
                        res.writeHead(413, { 'Content-Type': 'text/plain' });
                        res.end('Payload too large');
                    } catch (e) {}
                    try { req.destroy(); } catch (e) {}
                }
            };
            req.on('data', onData);

            // clean up listeners after response finishes
            res.on('close', () => req.removeListener('data', onData));
            res.on('finish', () => req.removeListener('data', onData));
        }

        // Set socket timeout
        try {
            req.socket.setTimeout(allowedTimeout, () => {
                try {
                    res.writeHead(504, { 'Content-Type': 'text/plain' });
                    res.end('Gateway timeout');
                } catch (e) {}
                try { req.destroy(); } catch (e) {}
            });
        } catch (e) {}

        // Forward request to leastConnections with per-request timeout
        leastConnections(clientServers, req, res, { proxyTimeout: allowedTimeout });
    } catch (e) {
        res.writeHead(500);
        res.end('[ERROR] Load balance error');
    }
});

loadBalance.listen(port, () => {
    console.log(`[INFO] Load balance started on port: ${port}`);
});