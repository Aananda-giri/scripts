should we chunk the description??

should we use qdrant over sql + pgvector??
yes

what embedding model??
nomic-embed-text-v1.5
- because it is lightweight and good at english
- Alternative: Qwen3-Embedding-0.6B: Heavier but better benchmarks

should we chunk at all??
- if description is small enough, we won't need chunking
  - experiments/field_length_report.txt shows that max. tokens count in description is ~400
- experiments/description_length_distribution.py shows ~90% of description have token len. <2000 tokens
- since we are using deepseek v4, which have context len. of 1M tokens, we will skip chunking initially



Embedding strategy:
embed the enriched text instead of only the description, something like:
```
Job Title: Senior Backend Engineer
Company: Acme
Location: Kathmandu
Level: Senior

Requirements:
- Python
- FastAPI
- AWS
```

place chunk  size in config

filter by metadata:
- extract metadata from query (using LLM) and filter by specific metadata for fields that are small set of unique values, like:
Job Category: 7 unique values
Job Level: 4 unique vallues
Tags: 4 unique values

Publication Date: we can extract: before, after values from query
    - all the dates seem to have consistent format (experiments/publication_date_format_report.py)
    - we can save the date-time in qdrant and filter using it

- Index these fields in qdrant, which would speed up our metadata filtering

how should we retrieve??
- extract filter
what to use embedding for and what to use text search??
title, location, level, 





## Future improvements
- implement chunking for description
- only split description, and duplicate all other fields rest of the entries across all chunks