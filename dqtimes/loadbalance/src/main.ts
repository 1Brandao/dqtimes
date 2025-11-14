import { createServer } from "http"
import { Server } from "./loadBalance/server";
import { leastConnections } from "./loadBalance/leastConnection";
import dotenv from "dotenv";
dotenv.config();

const port = Number(process.env.LB_PORT || 8000);
const clientServers: Server[] = process.env.CLIENT_SERVERS!
  .split(",")
  .map(url => ({ connections: 0, url }));

const loadBalance = createServer((req, res) => {
    try {
        leastConnections(clientServers, req, res);
    } catch (e) {
        res.writeHead(500);
        res.end('[ERROR] Load balance error');
    }
});

loadBalance.listen(port, () => {
    console.log(`[INFO] Load balance started on port: ${port}`);
});