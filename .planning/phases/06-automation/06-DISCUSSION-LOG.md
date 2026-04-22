# Phase 6: Automation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 06-automation
**Areas discussed:** Obsidian Ingest Frequency, Patch Monitor Logic, ngrok Purpose, n8n ↔ Backend Auth

---

## Area 1: Obsidian Ingest Frequency

| Option | Description | Selected |
|--------|-------------|----------|
| Scheduled (4-hour interval) | n8n cron trigger mỗi 4 tiếng | |
| Scheduled (once/day) | n8n cron trigger 1 lần/ngày | |
| File watcher | n8n theo dõi Obsidian vault directory thay đổi | |
| **Manual webhook trigger** | **n8n tạo webhook endpoint, user trigger bằng CLI/lệnh nhỏ khi cần** | **✅ Chọn** |
| n8n → backend webhook | Backend expose webhook, n8n trigger it | |

**User's choice:** Manual webhook trigger
**Notes:** User không muốn n8n chạy lịch cố định hay theo dõi file ngầm (sợ tốn tài nguyên). Muốn hoàn toàn làm chủ hệ thống — trigger thủ công khi cần.

---

## Area 2: Patch Monitor Logic

| Option | Description | Selected |
|--------|-------------|----------|
| **n8n giữ state** | Workflow lưu patch đã ingest vào node, so sánh mỗi lần | |
| **Backend giữ state** | Endpoint `/api/patch/current` trả về patch đã ingest, state trong DB/cache | **✅ Chọn** |

**User's choice:** Backend giữ state
**Notes:** Đảm bảo tính nhất quán dữ liệu. State sống trong DB cùng với chunks, dễ debug bằng curl, nhất quán và an toàn.

### CDN 403 Error Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Thử CommunityDragon fallback tự động | Tự động chuyển sang nguồn khác | |
| Bỏ qua và ghi log | Không làm gì, chỉ ghi log | |
| **Ghi log + Discord/Email notification** | **Bắn thông báo cho user biết để can thiệp thủ công** | **✅ Chọn** |

**User's choice:** Ghi log + Discord notification
**Notes:** User chọn Discord webhook cho notification. Không tự động fallback để tránh rủi ro sai data.

---

## Area 3: ngrok Purpose

| Option | Description | Selected |
|--------|-------------|----------|
| **Bỏ hoàn toàn** | **Không cần ngrok — 100% local, đơn giản và an toàn** | **✅ Chọn** |
| Chỉ expose n8n UI | Truy cập n8n từ bên ngoài | |
| Expose cả n8n + backend webhook | Full remote access | |

**User's choice:** Bỏ hoàn toàn
**Notes:** Hệ thống chạy 100% local, không cần truy cập từ xa, không có external webhook cần nhận. Giữ đơn giản, an toàn.

---

## Area 4: n8n ↔ Backend Auth

| Option | Description | Selected |
|--------|-------------|----------|
| **Không có auth** | Nội bộ Docker network, không ai bên ngoài reach được | |
| **API Key Bearer Token** | **Authorization: Bearer <SECRET> header trên ingest endpoints** | **✅ Chọn** |

**User's choice:** API Key Bearer Token Auth
**Notes:** Defense in Depth — ngay cả nội bộ cũng có auth. Future-proof nếu sau này cần mở port ra ngoài. API secret key lưu trong `.env` (backend) và n8n Credential (encrypted).

---

## Summary of Key Decisions

- **Obsidian ingest:** Manual webhook trigger (không lịch, không file watcher)
- **Patch monitor:** Backend giữ state + n8n workflow mỗi 6 tiếng + Discord notification khi CDN lỗi
- **ngrok:** Bỏ hoàn toàn
- **Auth:** Bearer token trên tất cả ingest endpoints
- **Notification:** Discord webhook (không email)

---

*Phase: 06-automation*
*Discussion date: 2026-04-22*
