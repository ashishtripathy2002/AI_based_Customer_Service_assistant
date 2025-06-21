"""Initialize indexes."""

from backend.doc_search.indexer import TranscriptIndex

# These two singletons will be shared everywhere
index_docs = TranscriptIndex(sug_type=0)
index_trans = TranscriptIndex(sug_type=1)
