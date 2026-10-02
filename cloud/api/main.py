#!/usr/bin/env python3
"""VORIX Cloud API"""
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os, json
from contextlib import asynccontextmanager
import asyncpg, redis.asyncio as redis

DB = os.getenv("DB_HOST", "postgres")
DBP = os.getenv("DB_PASS", "vorix")
RD = os.getenv("REDIS_HOST", "redis")
KEY = os.getenv("API_KEY", "dev")

pool = None
rds = None

@asynccontextmanager
async def lifespan(app):
    global pool, rds
    for i in range(20):
        try:
            pool = await asyncpg.create_pool(
                host=DB, database="vorix", user="vorix",
                password=DBP, min_size=2, max_size=15)
            break
        except Exception as e:
            print(f"[!] DB {i+1}: {e}")
            import asyncio
            await asyncio.sleep(3)

    async with pool.acquire() as c:
        await c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id BIGSERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ,
            agent_id TEXT,
            severity TEXT,
            gate TEXT,
            module TEXT,
            event_type TEXT,
            source_ip TEXT,
            country TEXT,
            message TEXT,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_ts ON logs(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_sev ON logs(severity);
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT,
            last_seen TIMESTAMPTZ,
            metadata JSONB
        );
        """)

    rds = redis.Redis(host=RD, port=6379, decode_responses=True)
    await rds.ping()
    print("[+] Ready")
    yield
    await pool.close()
    await rds.close()

app = FastAPI(title="VORIX", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class LogEntry(BaseModel):
    timestamp: str
    agent_id: str = "unknown"
    severity: str = "INFO"
    gate: str = ""
    module: str = ""
    event_type: str = ""
    message: str = ""
    source_ip: Optional[str] = None
    country: Optional[str] = None
    metadata: dict = {}

class HB(BaseModel):
    agent_id: str
    name: str
    version: str = "1.0"
    metadata: dict = {}

async def verify(x_api_key: str = Header(None)):
    if x_api_key != KEY:
        raise HTTPException(401, "Unauthorized")
    return True

@app.get("/")
async def root():
    return {"service": "VORIX", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.utcnow().isoformat()}

@app.post("/api/v1/logs")
async def ingest(log: LogEntry, _: bool = Depends(verify)):
    try:
        ts = datetime.fromisoformat(log.timestamp.replace("Z", "+00:00"))
    except:
        ts = datetime.utcnow()
    async with pool.acquire() as c:
        await c.execute("""
            INSERT INTO logs (timestamp, agent_id, severity, gate, module, event_type,
                             source_ip, country, message, metadata)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """, ts, log.agent_id, log.severity, log.gate, log.module, log.event_type,
            log.source_ip, log.country, log.message, json.dumps(log.metadata))
    return {"status": "ok"}

@app.post("/api/v1/logs/batch")
async def batch(logs: List[LogEntry], _: bool = Depends(verify)):
    n = 0
    async with pool.acquire() as c:
        async with c.transaction():
            for log in logs:
                try:
                    ts = datetime.fromisoformat(log.timestamp.replace("Z", "+00:00"))
                except:
                    ts = datetime.utcnow()
                try:
                    await c.execute("""
                        INSERT INTO logs (timestamp, agent_id, severity, gate, module, event_type,
                                         source_ip, country, message, metadata)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                    """, ts, log.agent_id, log.severity, log.gate, log.module, log.event_type,
                        log.source_ip, log.country, log.message, json.dumps(log.metadata))
                    n += 1
                except: pass
    return {"received": n}

@app.post("/api/v1/agent/heartbeat")
async def hb(h: HB, _: bool = Depends(verify)):
    async with pool.acquire() as c:
        await c.execute("""
            INSERT INTO agents (id, name, last_seen, metadata)
            VALUES ($1, $2, NOW(), $3)
            ON CONFLICT (id) DO UPDATE SET last_seen=NOW(), metadata=$3
        """, h.agent_id, h.name, json.dumps(h.metadata))
    return {"status": "ok"}

@app.get("/api/v1/stats")
async def stats(_: bool = Depends(verify)):
    async with pool.acquire() as c:
        t = await c.fetchval("SELECT COUNT(*) FROM logs")
        h = await c.fetchval("SELECT COUNT(*) FROM logs WHERE created_at > NOW() - INTERVAL '24 hours'")
        cr = await c.fetchval("SELECT COUNT(*) FROM logs WHERE severity='CRITICAL'")
        ag = await c.fetchval("SELECT COUNT(*) FROM agents WHERE last_seen > NOW() - INTERVAL '5 minutes'")
        ips = await c.fetch("SELECT source_ip, COUNT(*) as cnt FROM logs WHERE source_ip IS NOT NULL AND source_ip != '' GROUP BY source_ip ORDER BY cnt DESC LIMIT 10")
        cc = await c.fetch("SELECT country, COUNT(*) as cnt FROM logs WHERE country IS NOT NULL GROUP BY country ORDER BY cnt DESC LIMIT 10")
    return {
        "total": t or 0, "last_24h": h or 0, "critical": cr or 0,
        "agents": ag or 0,
        "top_ips": [dict(r) for r in ips],
        "countries": [dict(r) for r in cc],
    }

@app.get("/api/v1/logs")
async def get_logs(limit: int = 100, severity: str = None, _: bool = Depends(verify)):
    q = "SELECT * FROM logs WHERE 1=1"
    p = []
    if severity:
        p.append(severity)
        q += f" AND severity = ${len(p)}"
    p.append(limit)
    q += f" ORDER BY timestamp DESC LIMIT ${len(p)}"
    async with pool.acquire() as c:
        rows = await c.fetch(q, *p)
    return [dict(r) for r in rows]

@app.get("/api/v1/agents")
async def agents(_: bool = Depends(verify)):
    async with pool.acquire() as c:
        rows = await c.fetch("SELECT * FROM agents ORDER BY last_seen DESC")
    return [dict(r) for r in rows]
