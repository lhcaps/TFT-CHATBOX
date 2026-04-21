# Hướng dẫn xây dựng TFT Local Copilot cục bộ

## Tóm tắt điều hành

Bản build hợp lý nhất cho một **TFT Local Copilot** chạy trực tiếp trên máy cá nhân, đúng tinh thần “học và build thử, không overengineer”, là: **React + Vite + Tailwind** cho chat UI, **FastAPI** cho API và orchestration, **Ollama** chạy **native** trên máy để suy luận cục bộ, **Supabase local** chạy bằng **CLI** để có Postgres + pgvector + dashboard local, **n8n** chỉ dùng cho automation theo lịch và webhook, **Obsidian** đóng vai trò nguồn tri thức Markdown cá nhân, còn **ngrok** chỉ bật khi thật sự cần phơi webhook ra ngoài. Cách chia vai trò này bám rất sát khả năng thật của từng công cụ: Obsidian lưu note ở local vault dưới dạng Markdown/text file; Supabase CLI chạy toàn bộ stack local bằng `supabase init` và `supabase start`; Ollama phục vụ API local ở `http://localhost:11434`; n8n phù hợp cho cron/webhook hơn là làm app runtime chính. citeturn11search2turn22view2turn34search3turn34search0turn34search6turn23view0turn35view0

Với máy **64GB RAM + RTX 4070 Ti SUPER 16GB VRAM**, cấu hình “vừa đủ mà mạnh” cho MVP là: **`qwen3:8b`** làm model chat chính; **`qwen3-embedding:4b`** hoặc **`embeddinggemma`** làm model embedding; context ở mức **4K–8K** thay vì cố đẩy rất cao; chỉ giữ **một model sinh text + một model embedding** hoạt động thường xuyên; và dùng **HNSW** cho vector index. Về mặt artifact size chính thức, `qwen3:8b` khoảng **5.2GB**, `gemma3:12b` khoảng **8.1GB**, `qwen3-embedding:4b` khoảng **2.5GB**, `embeddinggemma` khoảng **622MB**; Ollama cũng cung cấp `ollama ps` hoặc `/api/ps` để kiểm tra `size_vram` thực tế sau khi load model. citeturn19search4turn19search0turn20view0turn20view1turn18search0turn34search8

Điểm quan trọng nhất về sản phẩm là **không nên biến MVP thành overlay “ra lệnh đánh như thế nào” hoặc tool trinh sát real-time đối thủ**. Chính sách TFT của entity["company","Riot Games","game developer"] nêu rõ các sản phẩm cung cấp thông tin động thời gian thực, scouting đối thủ, hoặc “dictate player decisions” là use-case không được chấp nhận khi public; còn các overlay/static tools dựa trên dữ liệu tĩnh trước trận hoặc lịch sử của chính người chơi mới là hướng an toàn hơn. Vì vậy, Local Copilot nên ưu tiên ba mode: **Normal** để hỏi đáp, **RAG** để truy hồi từ note/patch/meta/static data, và **Coach** để đưa ra **2–3 line of play có giải thích trade-off**, không phải một mệnh lệnh tuyệt đối. citeturn15search0

Bản thiết kế dưới đây giữ đúng tinh thần MVP “vừa đủ, không overengineer” của brief ban đầu. fileciteturn0file0

## Kiến trúc MVP đề xuất

Về kiến trúc, cách ít rủi ro nhất là **không nhét chat UI vào Obsidian ở giai đoạn đầu**. Obsidian nên là **knowledge source** để bạn viết note meta, comp notes, patch notes cá nhân, matchup note, còn chat UI nên là một web app riêng bằng React. Làm vậy bạn học được rõ ràng frontend/backend/RAG và tránh phải đụng sớm vào hệ sinh thái plugin của Obsidian. Obsidian vốn theo mô hình vault local, tự refresh khi file ngoài thay đổi, nên rất hợp để ingest định kỳ từ thư mục note thay vì làm giao diện chat chính. citeturn11search2turn11search3

Stack đề xuất cho MVP:

| Thành phần | Chọn gì | Vì sao chọn |
|---|---|---|
| Chat UI | React + Vite + Tailwind | Khởi tạo nhanh, dev server nhanh, CSS utility dễ ráp UI chat gọn. citeturn37search0turn29view0 |
| API | FastAPI | Dễ khai báo schema bằng Pydantic, hỗ trợ CORS rõ ràng, stream bằng `StreamingResponse`. citeturn25search1turn26search0turn36search0 |
| Model local | Ollama native | API local ổn định, stream mặc định, embed endpoint có batch array + custom dimensions. citeturn34search3turn34search0turn20view2turn33search0 |
| Database | Supabase local CLI | Chạy local stack rất nhanh, có Postgres + pgvector + dashboard, không cần tự dựng cả bó service bằng tay. citeturn22view2turn8search4 |
| Vectors | pgvector + HNSW | HNSW là lựa chọn mặc định được Supabase khuyến nghị cho ANN/vector search. citeturn22view0turn22view1 |
| Automation | n8n | Tốt cho cron ingest, patch check, webhook fan-out. citeturn35view0turn10search1turn10search0 |
| Notes | Obsidian | Markdown local, đọc file trực tiếp, hợp cho note/meta cá nhân. citeturn11search2turn11search1 |
| Tunnel | ngrok | Chỉ dùng khi cần phơi webhook local ra ngoài. citeturn12search1turn12search4 |

Mermaid sơ đồ kiến trúc:

```mermaid
flowchart LR
    U[Người dùng] --> FE[React + Vite + Tailwind Chat UI]
    FE -->|POST /api/chat/stream| BE[FastAPI]
    BE -->|/api/chat + /api/embed| OL[Ollama local]
    BE -->|SQL + RPC| DB[(Supabase local Postgres + pgvector)]

    OB[Obsidian Vault Markdown] --> ING[Python Ingest]
    TFT[Static TFT data<br/>Riot + CommunityDragon] --> ING
    ING --> DB

    N8N[n8n] -->|Schedule Trigger| ING
    N8N -->|HTTP webhook / patch automation| BE
    NG[ngrok] -->|Expose n8n webhook if needed| N8N
```

Thư mục dự án nên giữ rất phẳng:

```text
tft-local-copilot/
├─ apps/
│  ├─ backend/
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ config.py
│  │  │  ├─ db.py
│  │  │  ├─ models.py
│  │  │  ├─ prompts.py
│  │  │  ├─ routes/
│  │  │  │  ├─ chat.py
│  │  │  │  ├─ sessions.py
│  │  │  │  ├─ ingest.py
│  │  │  │  └─ health.py
│  │  │  ├─ services/
│  │  │  │  ├─ ollama.py
│  │  │  │  ├─ retrieval.py
│  │  │  │  └─ ranking.py
│  │  │  └─ utils/
│  │  │     ├─ markdown.py
│  │  │     └─ hashing.py
│  │  ├─ scripts/
│  │  │  ├─ ingest_obsidian.py
│  │  │  ├─ ingest_tft_static.py
│  │  │  └─ patch_refresh.py
│  │  ├─ requirements.txt
│  │  └─ Dockerfile
│  └─ frontend/
│     ├─ src/
│     │  ├─ components/
│     │  │  ├─ ChatShell.tsx
│     │  │  ├─ MessageList.tsx
│     │  │  ├─ Composer.tsx
│     │  │  ├─ ModeTabs.tsx
│     │  │  └─ CitationCard.tsx
│     │  ├─ api/
│     │  │  └─ chat.ts
│     │  ├─ App.tsx
│     │  ├─ main.tsx
│     │  └─ index.css
│     ├─ package.json
│     ├─ vite.config.ts
│     └─ Dockerfile
├─ infra/
│  ├─ docker-compose.yml
│  ├─ .env.example
│  └─ ngrok/
│     └─ refresh-webhook-url.sh
├─ n8n/
│  ├─ workflows/
│  │  ├─ obsidian_ingest.json
│  │  └─ patch_check.json
│  └─ local-files/
├─ supabase/
│  ├─ migrations/
│  └─ seed.sql
└─ docs/
   └─ tft-static-schema.json
```

## Chuẩn bị môi trường cục bộ

Phần này có một quyết định rất thực dụng: **containerize app và automation, nhưng để Ollama chạy native**. Lý do rất đơn giản: Ollama trên Windows chạy như ứng dụng native và hỗ trợ GPU NVIDIA/AMD; trên Linux có script cài chính thức + service systemd; còn API local vẫn đồng nhất ở `http://localhost:11434`. Làm vậy giảm cực nhiều ma sát GPU passthrough trong Docker và đúng với mục tiêu “học và ship nhanh”. citeturn34search3turn34search0turn34search6

### Các lệnh cài đặt tối thiểu

**Supabase local**

```bash
# trong root dự án
npx supabase init
npx supabase start
```

Supabase CLI tài liệu hóa rất rõ rằng chỉ với `supabase init` và `supabase start` bạn có thể chạy toàn bộ local stack; local dev mặc định cũng hướng tới loopback/local machine thay vì public internet, điều này phù hợp cho bản cục bộ. citeturn22view2turn7search1

**Ollama trên Windows**

```powershell
# cài bằng OllamaSetup.exe từ trang download
ollama -v
```

**Ollama trên Linux**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama -v
```

Ollama Windows cài native, chạy nền và phục vụ API ở `localhost:11434`; Linux có cả script cài chính thức lẫn hướng dẫn chạy service systemd. citeturn34search3turn34search0

**Model nên kéo trước**

```bash
ollama pull qwen3:8b
ollama pull gemma3:12b
ollama pull qwen3-embedding:4b
ollama pull embeddinggemma
```

Từ đây, cấu hình thực dụng nhất cho MVP là:
- **Mặc định**: `qwen3:8b`
- **Khi cần phân tích khó hơn**: `gemma3:12b`
- **Embedding mặc định**: `qwen3-embedding:4b`
- **Embedding siêu nhẹ**: `embeddinggemma` citeturn19search4turn19search0turn20view0turn20view1

### Chọn model cho cấu hình 64GB RAM và 16GB VRAM

Bảng dưới đây dùng **artifact size/context chính thức** từ thư viện model của Ollama; cột “đánh giá fit” là **suy luận vận hành** để chừa chỗ cho KV cache và context window. Khi cần số thật trên máy của bạn, kiểm tra bằng `ollama ps` hoặc `/api/ps`, vì Ollama trả ra cả `size_vram` và trạng thái CPU/GPU. citeturn19search4turn19search0turn20view0turn20view1turn18search0turn34search8

| Model | Artifact size chính thức | Context chính thức | Vai trò | Đánh giá fit trên 4070 Ti 16GB |
|---|---:|---:|---|---|
| `embeddinggemma` | 622MB | 2K | embedding siêu nhẹ | Rất dễ fit; phù hợp khi bạn muốn ingest nhanh, ít VRAM |
| `qwen3-embedding:4b` | 2.5GB | 40K | embedding tốt hơn, đa ngôn ngữ | Fit thoải mái; rất hợp cho RAG tiếng Việt + tiếng Anh |
| `qwen3:8b` | 5.2GB | 40K | chat model mặc định | Fit tốt; nên dùng 4K–8K context cho MVP |
| `gemma3:12b` | 8.1GB | 128K | chat/coach chất lượng hơn | Vẫn khả thi; chậm hơn `qwen3:8b` nhưng tốt cho phân tích |
| `qwen3:14b` | 9.3GB | 40K | chat mạnh hơn | Có thể chạy, nhưng sẽ sát hơn về VRAM và giảm headroom |
| `gemma3:27b` | 17GB | 128K | overkill cho MVP | Không phù hợp cho mục tiêu “vừa đủ” trên 16GB VRAM |

Khuyến nghị cuối cùng: **bắt đầu bằng `qwen3:8b` + `qwen3-embedding:4b`**. Khi phần backend, retrieval và UI đã ổn, mới thử `gemma3:12b` cho mode Coach. Đây là điểm cân bằng đẹp giữa tốc độ, chất lượng và sự “ít đau đầu” khi build. citeturn19search4turn19search0turn20view0

### Docker Compose tối thiểu

**Điểm quan trọng:** không nhét Supabase vào compose này. Hãy để **Supabase CLI** quản lý local stack của chính nó; compose chỉ cần lo app + n8n. Đây là lựa chọn ít rối nhất cho MVP. citeturn22view2turn23view0

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ../apps/backend
    container_name: tft-backend
    environment:
      APP_ENV: development
      APP_HOST: 0.0.0.0
      APP_PORT: 8000
      OLLAMA_BASE_URL: http://host.docker.internal:11434
      DATABASE_URL: postgresql://postgres:postgres@host.docker.internal:54322/postgres
      ALLOWED_ORIGINS: http://localhost:5173
      OBSIDIAN_VAULT_PATH: /vault
      EMBEDDING_MODEL: qwen3-embedding:4b
      EMBEDDING_DIMENSIONS: 1024
      CHAT_MODEL: qwen3:8b
    ports:
      - "8000:8000"
    volumes:
      - ../apps/backend:/app
      - ${OBSIDIAN_VAULT_PATH:-../vault}:/vault:ro
    command: >
      sh -c "pip install -r requirements.txt &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  frontend:
    build:
      context: ../apps/frontend
    container_name: tft-frontend
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    ports:
      - "5173:5173"
    volumes:
      - ../apps/frontend:/app
    command: >
      sh -c "npm install &&
             npm run dev -- --host 0.0.0.0 --port 5173"

  n8n:
    image: docker.n8n.io/n8nio/n8n
    container_name: tft-n8n
    ports:
      - "5678:5678"
    environment:
      N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS: "true"
      GENERIC_TIMEZONE: Asia/Ho_Chi_Minh
      TZ: Asia/Ho_Chi_Minh
      WEBHOOK_URL: ${WEBHOOK_URL:-http://localhost:5678/}
      N8N_PROXY_HOPS: "1"
    volumes:
      - n8n_data:/home/node/.n8n
      - ../n8n/local-files:/files

volumes:
  n8n_data:
```

FastAPI cần CORS explicit nếu frontend chạy khác origin; FastAPI khuyến nghị khai báo rõ `allow_origins` thay vì wildcard khi có credentials/header. n8n tài liệu hóa `WEBHOOK_URL`, `N8N_PROXY_HOPS`, timezone instance và Docker Compose config chính thức. citeturn26search0turn23view3turn32view0turn35view0

## Cơ sở dữ liệu và pipeline tri thức

MVP này cần đúng **bốn bảng lõi** mà bạn yêu cầu: `chat_sessions`, `chat_messages`, `documents`, `document_chunks`. Phần retrieval tốt nhất là lưu chunk text, metadata, `fts` tsvector và `embedding vector(1024)`. Lý do chọn **1024 chiều** là để vừa giữ HNSW index đơn giản dưới ngưỡng 2,000 dimensions, vừa tận dụng việc Ollama `/api/embed` hỗ trợ tham số `dimensions`; còn các model kiểu Qwen3 Embedding hỗ trợ output dimension linh hoạt. HNSW được Supabase khuyến nghị là lựa chọn mặc định; IVFFlat chỉ đáng cân nhắc khi dữ liệu lớn và bạn thật sự cần tối ưu kiểu khác. citeturn33search0turn20view0turn22view0turn22view1

### SQL schema và index

```sql
create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists chat_sessions (
  id uuid primary key default gen_random_uuid(),
  title text,
  mode text not null default 'normal'
    check (mode in ('normal', 'rag', 'coach')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists chat_messages (
  id bigserial primary key,
  session_id uuid not null references chat_sessions(id) on delete cascade,
  role text not null check (role in ('system', 'user', 'assistant', 'tool')),
  content text not null,
  citations jsonb not null default '[]'::jsonb,
  usage jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists chat_messages_session_created_idx
  on chat_messages(session_id, created_at);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  source_type text not null
    check (source_type in ('obsidian', 'tft_static', 'patch_note', 'manual')),
  source_path text not null,
  source_hash text not null,
  title text not null,
  season text,
  patch text,
  locale text not null default 'vi_VN',
  metadata jsonb not null default '{}'::jsonb,
  raw_markdown text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_type, source_path, source_hash)
);

create table if not exists document_chunks (
  id bigserial primary key,
  document_id uuid not null references documents(id) on delete cascade,
  chunk_index int not null,
  heading_path text,
  content text not null,
  token_estimate int,
  embedding vector(1024),
  metadata jsonb not null default '{}'::jsonb,
  fts tsvector generated always as (
    to_tsvector(
      'simple',
      coalesce(heading_path, '') || ' ' || coalesce(content, '')
    )
  ) stored,
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create index if not exists document_chunks_document_idx
  on document_chunks(document_id, chunk_index);

create index if not exists document_chunks_fts_idx
  on document_chunks using gin(fts);

create index if not exists document_chunks_embedding_hnsw_idx
  on document_chunks using hnsw (embedding vector_cosine_ops);
```

Phần full-text search dùng `tsvector`/GIN là hợp lý vì Supabase tài liệu hóa trực tiếp pipeline FTS của Postgres; phần vector search dùng HNSW + `vector_cosine_ops` vì Supabase hỗ trợ rõ operator class này cho cosine distance. citeturn8search6turn22view0

### Hàm truy hồi hybrid search

Supabase có ví dụ chính thức cho **hybrid search** dùng full-text + semantic search + Reciprocal Rank Fusion. Dưới đây là phiên bản thực dụng thu gọn cho `document_chunks`. citeturn21view2turn21view4

```sql
create or replace function hybrid_search_chunks(
  query_text text,
  query_embedding vector(1024),
  match_count int default 8,
  full_text_weight float default 1,
  semantic_weight float default 2,
  rrf_k int default 50
)
returns table (
  chunk_id bigint,
  document_id uuid,
  heading_path text,
  content text,
  metadata jsonb
)
language sql
as $$
with full_text as (
  select
    id,
    row_number() over (
      order by ts_rank_cd(fts, websearch_to_tsquery('simple', query_text)) desc
    ) as rank_ix
  from document_chunks
  where fts @@ websearch_to_tsquery('simple', query_text)
  limit least(match_count, 30) * 2
),
semantic as (
  select
    id,
    row_number() over (
      order by embedding <=> query_embedding
    ) as rank_ix
  from document_chunks
  where embedding is not null
  limit least(match_count, 30) * 2
)
select
  dc.id as chunk_id,
  dc.document_id,
  dc.heading_path,
  dc.content,
  dc.metadata
from full_text
full outer join semantic
  on full_text.id = semantic.id
join document_chunks dc
  on coalesce(full_text.id, semantic.id) = dc.id
order by
  coalesce(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
  coalesce(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight desc
limit least(match_count, 30);
$$;
```

Nếu bạn hỏi tôi chọn mặc định gì cho MVP, câu trả lời là:
- `match_count = 6..8`
- `semantic_weight = 2`
- `full_text_weight = 1`
- rerank cuối cùng bằng heuristic đơn giản ở app layer: ưu tiên chunk cùng patch/set, rồi mới đến cosine score.  

Lý do là dữ liệu TFT có rất nhiều tên riêng, nhưng người dùng cũng hay hỏi “ý nghĩa” hoặc “nên chơi thế nào”, nên semantic search cần được nhấn mạnh hơn. Đây là suy luận thiết kế dựa trên cách Supabase trộn RRF và đặc thù truy vấn game meta. citeturn21view2turn21view4

### Chiến lược ingest, chunking và embedding

Với Obsidian Markdown, bạn không nên dùng “cắt ẩu theo số ký tự” ngay từ đầu. Hướng hiệu quả hơn là:
1. bỏ qua `.obsidian/` và file không phải `.md`;
2. giữ lại frontmatter làm metadata;
3. tách note theo **heading hierarchy**;
4. trong mỗi section, chunk theo **fixed size có overlap**.  

Các tài liệu chính thống về RAG chunking đều nhấn mạnh rằng chunking nên giữ **semantic coherence**, và khi dùng fixed-size thì một thiết lập khởi đầu hợp lý là khoảng **512 tokens** với **25% overlap**. Nếu bạn không muốn kéo tokenizer riêng trong MVP, có thể dùng quy đổi thô khoảng **2,000 ký tự/chunk** với **500 ký tự overlap** làm bản đơn giản hóa chấp nhận được. citeturn31search0turn31search2turn31search3

Embedding pipeline nên làm theo lô vì Ollama `/api/embed` chấp nhận **một chuỗi hoặc một mảng chuỗi**, và trả lại `embeddings[][]`. Điều này cho phép bạn batch ingest rất sạch thay vì gọi model từng chunk một. Với 16GB VRAM, batch size **16** là điểm bắt đầu an toàn; nếu ổn, tăng lên **24–32**. citeturn33search0

### Python ingest script thực dụng

```python
# apps/backend/scripts/ingest_obsidian.py
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable

import asyncpg
import httpx

VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", "/vault"))
DATABASE_URL = os.getenv("DATABASE_URL")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:4b")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
CHUNK_CHARS = 2000
CHUNK_OVERLAP = 500
BATCH_SIZE = 16

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def walk_markdown_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.md"):
        if ".obsidian" not in p.parts:
            yield p

def split_sections(markdown: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(markdown))
    if not matches:
        return [("", markdown.strip())]

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        heading = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        if body:
            sections.append((heading, body))
    return sections

def fixed_chunks(text: str, chunk_chars: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    out = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_chars)
        out.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(0, end - overlap)
    return out

async def embed_batch(client: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    r = await client.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={
            "model": EMBEDDING_MODEL,
            "input": texts,
            "dimensions": EMBEDDING_DIMENSIONS,
            "truncate": True,
            "keep_alive": "15m",
        },
        timeout=180.0,
    )
    r.raise_for_status()
    return r.json()["embeddings"]

async def main() -> None:
    conn = await asyncpg.connect(DATABASE_URL)
    client = httpx.AsyncClient()

    try:
        for md_file in walk_markdown_files(VAULT_PATH):
            raw = md_file.read_text(encoding="utf-8", errors="ignore")
            source_hash = sha256_text(raw)

            doc_id = await conn.fetchval(
                """
                insert into documents (source_type, source_path, source_hash, title, raw_markdown, metadata)
                values ($1, $2, $3, $4, $5, $6)
                on conflict (source_type, source_path, source_hash)
                do update set updated_at = now()
                returning id
                """,
                "obsidian",
                str(md_file.relative_to(VAULT_PATH)),
                source_hash,
                md_file.stem,
                raw,
                json.dumps({"path": str(md_file)}),
            )

            await conn.execute("delete from document_chunks where document_id = $1", doc_id)

            chunk_rows: list[tuple[int, str, str]] = []
            chunk_index = 0
            for heading, body in split_sections(raw):
                for chunk in fixed_chunks(body):
                    chunk_rows.append((chunk_index, heading, chunk))
                    chunk_index += 1

            for i in range(0, len(chunk_rows), BATCH_SIZE):
                batch = chunk_rows[i:i + BATCH_SIZE]
                texts = [f"{heading}\n\n{content}" if heading else content for _, heading, content in batch]
                vectors = await embed_batch(client, texts)

                for (idx, heading, content), vector in zip(batch, vectors):
                    await conn.execute(
                        """
                        insert into document_chunks
                          (document_id, chunk_index, heading_path, content, token_estimate, embedding, metadata)
                        values ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        doc_id,
                        idx,
                        heading,
                        content,
                        max(1, len(content) // 4),
                        vector,
                        json.dumps({"source": "obsidian"}),
                    )
    finally:
        await client.aclose()
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Code này cố tình “đủ dùng”: đọc vault, hash file, tách section theo heading, chunk fixed-size có overlap, batch embed, và nạp vào Postgres. Nó không cố làm semantic parser phức tạp vì MVP chưa cần. Khối lượng tri thức ban đầu của bạn chủ yếu là patch note cá nhân, comp note và static TFT data, không phải hàng trăm nghìn PDF. citeturn11search2turn33search0turn31search2

## Backend FastAPI và giao diện React

FastAPI rất hợp cho bài toán này vì phần **request schema** và **response schema** viết bằng Pydantic rất rõ, còn streaming thì dùng `StreamingResponse`. Về CORS, FastAPI khuyến nghị khai báo origin cụ thể; về request body, Pydantic model là cách chuẩn; về stream, `StreamingResponse` là response class phù hợp để đẩy chunk ra dần. citeturn25search1turn26search0turn36search0turn36search2

### Contract endpoint đề xuất

| Route | Method | Mục đích |
|---|---|---|
| `/health` | GET | Healthcheck app, DB, Ollama |
| `/api/sessions` | POST | Tạo session chat mới |
| `/api/sessions` | GET | Liệt kê session gần đây |
| `/api/sessions/{session_id}/messages` | GET | Lấy lịch sử chat |
| `/api/chat` | POST | Chat non-streaming |
| `/api/chat/stream` | POST | Chat streaming dạng SSE |
| `/api/search` | POST | Debug retrieval |
| `/api/ingest/obsidian` | POST | Re-ingest vault Obsidian |
| `/api/ingest/tft-static` | POST | Nạp/chuẩn hóa static TFT JSON |

Schema request/response thực dụng:

```python
# apps/backend/app/models.py
from __future__ import annotations
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

Mode = Literal["normal", "rag", "coach"]
Role = Literal["user", "assistant", "system", "tool"]

class SessionCreate(BaseModel):
    title: Optional[str] = None
    mode: Mode = "normal"

class SessionOut(BaseModel):
    id: str
    title: Optional[str] = None
    mode: Mode

class MessageOut(BaseModel):
    role: Role
    content: str
    citations: list[dict[str, Any]] = Field(default_factory=list)

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    mode: Mode = "rag"
    top_k: int = 6
    patch: Optional[str] = None
    season: Optional[str] = None
    stream: bool = True

class SearchRequest(BaseModel):
    query: str
    top_k: int = 8
```

### Template prompt cho ba mode

Điểm khác biệt giữa ba mode không nên nằm ở “văn phong”, mà nằm ở **quy tắc ra quyết định**.

```python
# apps/backend/app/prompts.py
NORMAL_SYSTEM = """
Bạn là TFT Local Copilot.
Trả lời ngắn gọn, rõ ràng, thực dụng.
Nếu thiếu dữ liệu thì nói rõ phần nào là suy luận.
"""

RAG_SYSTEM = """
Bạn là TFT Local Copilot dùng RAG.
Chỉ khẳng định mạnh khi thông tin có trong ngữ cảnh truy hồi.
Ưu tiên trả lời theo patch/set hiện tại nếu metadata có sẵn.
Nếu tài liệu mâu thuẫn, nêu rõ mâu thuẫn và chọn tài liệu mới hơn.
Trích nguồn theo [doc:title > heading].
"""

COACH_SYSTEM = """
Bạn là TFT Coach cục bộ.
Không ra lệnh một chiều.
Luôn đưa 2-3 line of play với:
- điều kiện vào bài
- lợi ích
- rủi ro
- pivot fallback
Nếu câu hỏi liên quan quyết định trong trận, ưu tiên:
econ -> tempo -> cap board -> contest risk.
Không dùng thông tin scout đối thủ theo thời gian thực nếu người dùng không tự cung cấp.
"""

USER_TEMPLATE = """
Ngữ cảnh trận:
- patch: {patch}
- season: {season}
- mode: {mode}

Câu hỏi người chơi:
{question}
"""

RAG_CONTEXT_TEMPLATE = """
Ngữ cảnh truy hồi:
{contexts}
"""
```

Ví dụ prompt thực dụng cho TFT:
- “Tôi đang level 7, 42 máu, có 2 bản Yasuo và 1 ấn Dark Star. Có nên roll xuống 20 hay fast 8?”
- “Comp N.O.V.A. đang bị contest 3 nhà ở Space Gods. Hãy cho tôi 3 pivot line hợp lý nhất.”
- “Patch 17.1, nếu opener thiên về item AP nhưng shop lại ra nhiều frontliner, tôi nên chuyển sang line nào?”  

Cách đặt prompt này khớp với chính sách TFT công khai hơn vì nó **gợi ý line of play có điều kiện**, không biến công cụ thành “phần mềm ra lệnh” hoặc “trợ lý gian lận”. citeturn15search0turn17search0turn16search4

### FastAPI handler cho streaming

Ollama stream theo **NDJSON** mặc định ở `/api/chat`; trong FastAPI ta chỉ cần bọc lại thành **SSE text/event-stream** để frontend render realtime. Ollama cũng hỗ trợ `keep_alive`, `stream`, `think`, các usage field ở chunk cuối. citeturn20view2turn18search8turn18search9turn18search4turn33search7

```python
# apps/backend/app/routes/chat.py
from __future__ import annotations
import json
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models import ChatRequest

router = APIRouter()

OLLAMA_BASE_URL = "http://localhost:11434"
CHAT_MODEL = "qwen3:8b"

def sse(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")

@router.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    async def gen():
        # chỗ này bạn thay bằng retrieval + prompt thật
        messages = [
            {"role": "system", "content": "Bạn là TFT Local Copilot."},
            {"role": "user", "content": req.message},
        ]

        assistant_text = []

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": CHAT_MODEL,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": "15m",
                    "options": {"num_ctx": 8192},
                },
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line:
                        continue

                    chunk = json.loads(line)
                    message = chunk.get("message", {})
                    delta = message.get("content", "")

                    if delta:
                        assistant_text.append(delta)
                        yield sse("token", {"delta": delta})

                    if chunk.get("done") is True:
                        yield sse("done", {
                            "content": "".join(assistant_text),
                            "usage": {
                                "total_duration": chunk.get("total_duration"),
                                "load_duration": chunk.get("load_duration"),
                                "prompt_eval_count": chunk.get("prompt_eval_count"),
                                "eval_count": chunk.get("eval_count"),
                            }
                        })
                        break

    return StreamingResponse(gen(), media_type="text/event-stream")
```

### React chat UI và cách đọc SSE bằng `fetch`

Về phía frontend, **EventSource** là API SSE chuẩn nhưng bản chất là kênh **một chiều từ server sang browser** với URL-based connection; cho chat app cần body POST phức tạp, cách ít rắc rối nhất là dùng **`fetch` + `ReadableStream.getReader()`** và parse event stream thủ công. Vite là lựa chọn scaffolding rất nhanh; Tailwind v4 hỗ trợ plugin Vite chính thức; các utility như `overflow-y-auto` và `dark:*` là đủ cho một chat shell gọn. citeturn30search0turn30search2turn30search6turn37search0turn29view0turn27search1turn27search2

```tsx
// apps/frontend/src/components/ChatShell.tsx
import { useRef, useState } from "react";

type Msg = { role: "user" | "assistant"; content: string };

export default function ChatShell() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"normal" | "rag" | "coach">("rag");
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  async function send() {
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userText }, { role: "assistant", content: "" }]);
    setLoading(true);

    const controller = new AbortController();
    abortRef.current = controller;

    const res = await fetch("http://localhost:8000/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText, mode, stream: true }),
      signal: controller.signal,
    });

    if (!res.body) {
      setLoading(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const evt of parts) {
        const lines = evt.split("\n");
        const event = lines.find((l) => l.startsWith("event:"))?.replace("event:", "").trim();
        const dataLine = lines.find((l) => l.startsWith("data:"))?.replace("data:", "").trim();
        if (!event || !dataLine) continue;

        const data = JSON.parse(dataLine);

        if (event === "token") {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              ...next[next.length - 1],
              content: next[next.length - 1].content + data.delta,
            };
            return next;
          });
        }

        if (event === "done") {
          setLoading(false);
        }
      }
    }

    setLoading(false);
  }

  return (
    <div className="mx-auto flex h-screen max-w-5xl flex-col bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      <header className="border-b border-gray-200 p-4 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">TFT Local Copilot</h1>
          <div className="flex gap-2">
            {(["normal", "rag", "coach"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`rounded-xl px-3 py-1 text-sm ${mode === m ? "border border-gray-900 dark:border-gray-100" : "border border-gray-300 dark:border-gray-700"}`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              msg.role === "user"
                ? "ml-auto bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900"
                : "bg-gray-100 dark:bg-gray-900"
            }`}
          >
            <div className="mb-1 text-xs opacity-60">{msg.role}</div>
            <div className="whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}
      </main>

      <footer className="border-t border-gray-200 p-4 dark:border-gray-800">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={3}
            className="flex-1 rounded-2xl border border-gray-300 bg-transparent p-3 outline-none dark:border-gray-700"
            placeholder="Hỏi về comp, pivot, item, patch, augment..."
          />
          <div className="flex flex-col gap-2">
            <button onClick={send} className="rounded-2xl border px-4 py-2">Gửi</button>
            <button onClick={() => abortRef.current?.abort()} className="rounded-2xl border px-4 py-2">Dừng</button>
          </div>
        </div>
      </footer>
    </div>
  );
}
```

Khởi tạo frontend mới:

```bash
npm create vite@latest apps/frontend -- --template react-ts
cd apps/frontend
npm install
npm install tailwindcss @tailwindcss/vite
npm run dev
```

`vite build` xuất static bundle từ entry `index.html`, còn Tailwind v4 có plugin Vite chính thức và chỉ cần `@import "tailwindcss";` trong CSS. citeturn37search0turn29view0turn37search1turn37search2

## Dữ liệu TFT và tự động hóa cập nhật

Nguồn dữ liệu TFT nên được chia rất rạch ròi thành hai lớp.

Lớp thứ nhất là **nguồn chính thức** từ hệ sinh thái TFT của entity["company","Riot Games","game developer"]: API policy, routing, match history, Data Dragon versions, và các file static như `tft-champion.json`, `tft-item.json`, `tft-trait.json`, `tft-augments.json`. Riot cũng nói rõ rằng cập nhật Data Dragon sau patch là **thủ công**, nên có thể không lên ngay tức thì sau mỗi patch. citeturn15search0

Lớp thứ hai là **entity["organization","CommunityDragon","lol asset archive"]** dùng làm “fast path” cho asset/data mới hơn, đặc biệt khi bạn cần raw JSON và localization `vi_vn`. CommunityDragon tài liệu hóa rằng họ cung cấp nhiều JSON data cho TFT; thư mục `raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/vi_vn/v1/` hiện có các file như `tftcontentdata.json`, `tftitems.json`, `tfttraits.json`, `tftsets.json`. Đây là nguồn cực tiện để build pipeline cập nhật nhanh, nhưng vì không phải source-of-truth chính thức, bạn vẫn nên ưu tiên Riot Data Dragon/API khi có xung đột nội dung gameplay cốt lõi. citeturn14search0turn14search1turn14search2

Hiện tại, ví dụ bạn nêu là **Set 17: Space Gods** không còn là giả định nữa mà đã là set hiện hành trên site chính thức TFT, live từ patch **17.1 ngày 15/04/2026**; bản localized `vi-vn` của trang tin TFT cũng đã có bài viết cho mùa 17. Điều này làm ví dụ “quy trình thêm mùa mới” ở dưới rất thực tế chứ không còn mang tính minh họa suông. citeturn17search4turn17search1

### JSON schema cho static data nội bộ

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TFTSetBundle",
  "type": "object",
  "required": ["set", "patch", "locale", "champions", "traits", "items", "augments"],
  "properties": {
    "set": { "type": "string" },
    "patch": { "type": "string" },
    "locale": { "type": "string" },
    "champions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "cost", "traits"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "cost": { "type": "integer" },
          "traits": { "type": "array", "items": { "type": "string" } },
          "ability": { "type": "string" },
          "stats": { "type": "object" },
          "source_url": { "type": "string" }
        }
      }
    },
    "traits": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "breakpoints": { "type": "array", "items": { "type": "integer" } },
          "description": { "type": "string" },
          "source_url": { "type": "string" }
        }
      }
    },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "recipe": { "type": "array", "items": { "type": "string" } },
          "description": { "type": "string" },
          "source_url": { "type": "string" }
        }
      }
    },
    "augments": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "tier": { "type": "string" },
          "description": { "type": "string" },
          "source_url": { "type": "string" }
        }
      }
    }
  }
}
```

### Quy trình thêm mùa mới hoặc patch mới

Với ví dụ **Season 17 Space Gods**, quy trình cập nhật nên là:

1. **Cập nhật source config**: patch hiện tại, set hiện tại, locale ưu tiên (`vi_vn`, fallback `default`/`en_us`). Dùng `versions.json` của Data Dragon để kiểm tra patch chính thức, nhưng luôn nhớ Riot cảnh báo DDragon có thể lên chậm. citeturn15search0  
2. **Kéo static data**:  
   - Riot: `tft-champion.json`, `tft-item.json`, `tft-trait.json`, `tft-augments.json`  
   - CommunityDragon: `tftcontentdata.json`, `tftitems.json`, `tfttraits.json`, `tftsets.json` từ `latest` hoặc `vi_vn` nếu có. citeturn15search0turn14search1turn14search2  
3. **Normalize** về schema nội bộ ở trên.  
4. **Tạo documents** theo loại `tft_static` và `patch_note`.  
5. **Chunk + embed lại** tất cả document bị đổi hash.  
6. **Rebuild / analyze index** nếu số chunk tăng mạnh.  
7. **Sanity check**: tổng số tướng, tộc/hệ, item, augment có hợp lý không; các link asset có còn sống không.  

Patch release checklist chi tiết ở phần cuối.

### n8n workflow cho ingest định kỳ

n8n có **Schedule Trigger** để chạy cron/workflow theo giờ cố định; node này phụ thuộc timezone của workflow hoặc timezone của instance, và workflow cần được **publish** thì schedule mới chạy. Đây là lý do bạn nên set rõ `GENERIC_TIMEZONE=Asia/Ho_Chi_Minh`. citeturn35view0turn35view2

Workflow ingest Obsidian rút gọn:

```json
{
  "name": "obsidian_ingest_every_4h",
  "nodes": [
    {
      "name": "Every 4 Hours",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 4
            }
          ]
        }
      }
    },
    {
      "name": "Call Backend Ingest",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://host.docker.internal:8000/api/ingest/obsidian",
        "sendBody": true,
        "contentType": "json",
        "specifyBody": "json",
        "jsonBody": "{\"full\":true}"
      }
    }
  ]
}
```

Workflow patch check rút gọn:

```json
{
  "name": "tft_patch_check",
  "nodes": [
    {
      "name": "Every 6 Hours",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "cronExpression": "0 */6 * * *"
        }
      }
    },
    {
      "name": "Get Riot Versions",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "https://ddragon.leagueoflegends.com/api/versions.json"
      }
    },
    {
      "name": "Get CDragon TFT Listing",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/vi_vn/v1/"
      }
    },
    {
      "name": "Decide Refresh",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "language": "javaScript",
        "jsCode": "return items;"
      }
    },
    {
      "name": "Refresh Static Data",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://host.docker.internal:8000/api/ingest/tft-static",
        "sendBody": true,
        "contentType": "json",
        "specifyBody": "json",
        "jsonBody": "{\"source\":\"patch-check\"}"
      }
    }
  ]
}
```

Node **HTTP Request** là node chính thức để gọi REST API; node **Code** là nơi phù hợp để so patch/version/hash rồi quyết định có refresh hay không. citeturn10search1turn10search0

### ngrok để expose webhook local

Ngrok tạo secure tunnel từ internet vào localhost; với local app/Webhook, lệnh cơ bản là `ngrok http <port>`. Ngrok Agent còn có **local API** tại `http://127.0.0.1:4040/api`, nơi bạn có thể đọc `public_url` và refresh cấu hình cho n8n. Đồng thời, n8n yêu cầu `WEBHOOK_URL` và `N8N_PROXY_HOPS=1` khi chạy sau reverse proxy/tunnel. citeturn12search4turn12search1turn32view2turn32view3turn32view0

```bash
ngrok config add-authtoken <TOKEN>
ngrok http 5678
curl http://127.0.0.1:4040/api/tunnels
```

Script auto-refresh URL webhook cho n8n:

```bash
#!/usr/bin/env bash
set -euo pipefail

PUBLIC_URL=$(
  curl -s http://127.0.0.1:4040/api/tunnels \
    | jq -r '.tunnels[] | select(.proto=="https") | .public_url' \
    | head -n 1
)

if [ -z "${PUBLIC_URL}" ]; then
  echo "Không tìm thấy ngrok public_url"
  exit 1
fi

cat > ./infra/.env.ngrok <<EOF
WEBHOOK_URL=${PUBLIC_URL}/
N8N_PROXY_HOPS=1
EOF

docker compose --env-file ./infra/.env.ngrok -f ./infra/docker-compose.yml up -d --force-recreate n8n

echo "WEBHOOK_URL đã cập nhật thành ${PUBLIC_URL}/"
```

Lưu ý thẳng: nếu bạn dùng domain ngẫu nhiên của ngrok free tier, URL sẽ đổi khi restart tunnel; khi đó mọi dịch vụ ngoài hoặc webhook registry phụ thuộc URL cũ phải được cập nhật lại. Nếu workflow của bạn sống lâu, dùng domain ổn định sẽ đỡ phiền hơn. Ngrok docs cũng nói rõ agent endpoint tồn tại theo vòng đời của process đang chạy. citeturn12search0turn12search4turn32view2turn32view3

## Vận hành, hiệu năng, bảo mật và checklist

### Tối ưu hiệu năng

Đừng tối ưu quá sớm. Với MVP, năm đòn bẩy hiệu năng đáng tiền nhất là:

Thứ nhất, **giới hạn context**. Ollama mặc định dùng context khoảng **4096 tokens**, có thể tăng bằng `OLLAMA_CONTEXT_LENGTH` hoặc `num_ctx`, nhưng đừng đẩy quá cao từ ngày đầu. Với chat kiểu TFT, 4K–8K là đủ cho đa số truy vấn nếu retrieval đã làm đúng việc. citeturn34search8

Thứ hai, **giữ model trong RAM/VRAM vừa đủ lâu**. Ollama mặc định giữ model trong bộ nhớ khoảng **5 phút**; bạn có thể dùng `keep_alive` để tránh reload liên tục hoặc unload ngay sau request khi cần giải phóng tài nguyên. citeturn18search4

Thứ ba, **batch embedding** thay vì bắn lẻ. `/api/embed` hỗ trợ array input, nhờ vậy tốc độ ingest tăng rõ rệt và giảm overhead HTTP. citeturn33search0

Thứ tư, **ưu tiên HNSW trước IVFFlat**. Supabase khuyến nghị HNSW là lựa chọn mặc định, còn IVFFlat nên dùng khi bạn có lý do rõ ràng và hiểu việc đánh đổi recall/speed/probes/lists. citeturn22view0turn22view1

Thứ năm, **cache những gì lặp lại**. Cụ thể:
- cache embedding của query giống hệt nhau trong 10–30 phút;
- cache kết quả search cho `(query, mode, patch, season)` rất ngắn;
- cache static TFT JSON đã normalize trên đĩa.  

Bạn chưa cần Redis. In-memory LRU hoặc file cache là đủ cho bản local.

### Bảo mật và quyền riêng tư

Nếu mục tiêu là **local-only**, bạn có ba nguyên tắc sống còn.

Một là, **không public Ollama**. Ollama docs nói rõ local API `localhost:11434` **không yêu cầu auth** khi truy cập local. Tức là nếu bạn tự expose bừa cổng này ra mạng, bạn đang tự mở một model server không auth. citeturn33search5

Hai là, **không để key Riot hoặc service credential ở frontend**. Riot nhấn mạnh API key không được nhúng trong code phân phối public; với local app vẫn nên giữ key ở backend/env var. citeturn15search0

Ba là, **ngrok agent API local không có auth** và chạy trên local inspection interface. Điều đó ổn trong localhost, nhưng bạn không nên bind nó ra mạng hoặc tunnel tiếp cổng 4040. citeturn32view2turn32view4

### Lỗi thường gặp và cách xử lý

Nếu **Ollama chạy CPU thay vì GPU**, kiểm tra `ollama ps` hoặc `/api/ps` để xem `Processor`/`size_vram`; trên Linux, docs của Ollama còn ghi nhận trường hợp resume từ suspend làm mất NVIDIA UVM và fallback CPU. citeturn34search8turn18search0turn34search4

Nếu **CORS fail** giữa React và FastAPI, đừng dùng wildcard bừa. Khai báo đúng origin `http://localhost:5173`, headers và methods cần thiết. FastAPI nói rõ wildcard không phải lúc nào cũng hợp lệ khi dùng credentials. citeturn26search0

Nếu **n8n webhook URL sai** khi chạy sau ngrok, set lại `WEBHOOK_URL`, `N8N_PROXY_HOPS=1`, rồi recreate container n8n. Đây là lỗi rất hay gặp và docs của n8n nói thẳng luôn. citeturn32view0turn32view1

Nếu **Data Dragon chưa có patch mới**, đừng hoảng. Riot chính thức nói DDragon có thể cập nhật thủ công và không phải lúc nào cũng lên ngay; lúc đó dùng CommunityDragon `latest` làm staging source, rồi hợp thức hóa lại khi Riot data lên. citeturn15search0turn14search2

Nếu **tạo HNSW index bị lỗi vì vector quá dài**, nguyên nhân thường là dimension vượt ngưỡng indexable. Supabase tài liệu hóa giới hạn HNSW trên `vector` tới **2,000 dimensions**; giải pháp thực dụng cho MVP là dùng `dimensions: 1024` ngay từ `/api/embed`. citeturn22view0turn33search0

### Checklist cập nhật patch

Khi TFT ra patch mới, checklist tốt nhất là:

| Việc cần làm | Kết quả mong muốn |
|---|---|
| Kiểm tra `versions.json` của Riot | Biết patch chính thức mới nhất |
| Kiểm tra `raw.communitydragon.org/latest/.../tft*.json` | Biết dữ liệu raw đã nhảy hay chưa |
| Tải lại champions / traits / items / augments | Có static bundle mới |
| Normalize về schema nội bộ | Không thay API app |
| So hash với dữ liệu cũ | Chỉ re-embed phần đổi |
| Re-ingest `documents` và `document_chunks` | Retrieval dùng dữ liệu mới |
| Test 10 câu hỏi smoke-test | Không có drift nghiêm trọng |
| Gắn `patch` vào metadata chunks | Coach/RAG ưu tiên patch đúng |
| Xuất lại changelog nội bộ ở Obsidian | Có source giải thích cho RAG |
| Nếu dùng ngrok webhook | Kiểm tra URL sống và n8n publish lại nếu cần |

### Lộ trình ưu tiên theo ngày

| Mốc | Việc làm | Deliverable |
|---|---|---|
| Day 1 | Khởi tạo repo, cài Ollama, kéo model, `supabase init/start`, scaffold Vite + Tailwind, tạo FastAPI app skeleton | App chạy rỗng: frontend 5173, backend 8000, Ollama 11434, Supabase local lên |
| Day 2 | Viết schema SQL, tạo bảng, healthcheck DB/Ollama, route `/api/sessions` và `/api/chat` non-stream | Chat non-streaming hoạt động |
| Day 3 | Viết `/api/chat/stream`, parse stream ở React, hoàn thiện UI chat shell cơ bản | Chat streaming realtime |
| Day 4 | Viết ingest Obsidian, chunking theo heading + overlap, embed batch, hybrid search SQL | RAG trả lời được từ note cá nhân |
| Day 5 | Nạp static TFT JSON, thêm metadata `patch`, `season`, mode `coach`, prompt templates | Hỏi comp/item/augment từ static data |
| Day 6 | Dựng n8n ingest theo lịch, workflow patch check, script ngrok refresh URL | Automation chạy được |
| Day 7 | Tune top-k, weights, caching, smoke-test 20 câu hỏi, dọn lỗi CORS/webhook/GPU | MVP tương đối ổn định |
| Day 7+ | Bổ sung match-history cá nhân, citation UI, evaluation set, export/import notes | Bản v2 có chiều sâu hơn |

### Nguồn ưu tiên để tra cứu tiếp

Khi bạn kẹt kỹ thuật, hãy ưu tiên mở theo thứ tự này:

- **Ollama docs**: install, `/api/chat`, `/api/embed`, streaming, `keep_alive`, `ollama ps`. citeturn34search0turn34search3turn20view2turn33search0turn18search8turn18search4turn34search8  
- **Supabase docs**: local CLI, pgvector, HNSW, hybrid search. citeturn22view2turn8search4turn22view0turn21view2  
- **n8n docs**: Docker Compose, `WEBHOOK_URL`, Schedule Trigger, HTTP Request, Code node. citeturn23view0turn32view0turn35view0turn10search1turn10search0  
- **FastAPI docs**: request body model, CORS, `StreamingResponse`. citeturn25search1turn26search0turn36search0  
- **Vite + Tailwind docs**: scaffold project, plugin Tailwind v4 cho Vite. citeturn37search0turn29view0  
- **TFT/Riot docs**: chính sách API, static data/patch/version, set overview. citeturn15search0turn17search4turn17search1  
- **CommunityDragon**: raw JSON/asset listing và locale `vi_vn`. citeturn14search0turn14search1turn14search2

Kết luận thẳng: nếu bạn muốn **học đúng phần cốt lõi** mà vẫn build được một sản phẩm usable ngay trên máy, đừng làm “siêu kiến trúc”. Hãy chốt bằng bộ sau: **Ollama native + FastAPI + React/Vite/Tailwind + Supabase local CLI + Obsidian ingest + n8n cron + ngrok khi cần**. Đó là con đường ngắn nhất để có một **TFT Local Copilot** thực sự chạy được, dễ debug, dễ mở rộng, và vẫn đủ “ngầu” để bạn học trọn chuỗi từ UI đến RAG, automation và dữ liệu game. citeturn11search2turn22view2turn34search3turn34search0turn23view0turn12search4