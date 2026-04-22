-- Ensure fts generated column exists (backwards compat: if table was created before fts was added)
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS fts tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

-- Recreate fts index (handles both fresh and upgraded schemas)
DROP INDEX IF EXISTS chunks_content_fts_idx;
CREATE INDEX IF NOT EXISTS chunks_content_fts_idx ON chunks USING gin (fts);

CREATE OR REPLACE FUNCTION hybrid_search_chunks(
  query_text text,
  query_embedding vector(1024),
  match_count int default 8,
  full_text_weight float default 1,
  semantic_weight float default 2,
  rrf_k int default 50
)
RETURNS TABLE (
  chunk_id bigint,
  document_id uuid,
  heading_path text,
  content text,
  metadata jsonb
)
LANGUAGE sql
AS $$
with full_text as (
  select
    id,
    row_number() over (
      order by ts_rank_cd(fts, websearch_to_tsquery('simple', query_text)) desc
    ) as rank_ix
  from chunks
  where fts @@ websearch_to_tsquery('simple', query_text)
  limit least(match_count, 30) * 2
),
semantic as (
  select
    id,
    row_number() over (
      order by embedding <=> query_embedding
    ) as rank_ix
  from chunks
  where embedding is not null
  limit least(match_count, 30) * 2
)
select
  c.id as chunk_id,
  null::uuid as document_id,
  null::text as heading_path,
  c.content,
  c.metadata
from full_text
full outer join semantic
  on full_text.id = semantic.id
join chunks c
  on coalesce(full_text.id, semantic.id) = c.id
order by
  coalesce(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
  coalesce(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight desc
limit least(match_count, 30);
$$;
