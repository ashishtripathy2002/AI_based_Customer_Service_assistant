"""Doc Search Pipeline."""

from prefect import flow, task

from backend.doc_search import index_docs, index_trans


@task
def load_transcript_index() -> str:
    """Load the transcript index."""
    index_trans.load()
    return "Transcript index loaded"


@task
def load_doc_index() -> str:
    """Load the document index."""
    index_docs.load()
    return "Document index loaded"


@flow(name="Document Indexing Flow")
def indexing_flow() -> tuple[str, str]:
    """Run the document and transcript indexing flow."""
    doc_msg = load_doc_index()
    trans_msg = load_transcript_index()
    return doc_msg, trans_msg


if __name__ == "__main__":
    indexing_flow()
