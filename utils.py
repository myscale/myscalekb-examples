import re
from typing import Dict


def process_answer_references(answer: str, retrieved_docs: dict):
    """
    Process citation box [citation:x], Extract 'x' and correspond it to the `citation_id` in the retrieved docs
    :param answer: The original model answer
    :param retrieved_docs: Retrieved doc chunks and doc metadata
    :return:
    """
    # Extracting [citation:x] using regular expressions,
    # Sometimes the output of llm does not completely follow the instruction.
    # Use post-processing to improve the robustness of citation processing.
    citations = re.findall(
        r'\[( )?citation:(\d+)( )?]|\[( )?引用:(\d+)( )?]|\[( )?chunk:(\d+)( )?]|\[( )?ChunkId:(\d+)( )?]|【( )?citation:(\d+)( )?】',
        answer, re.IGNORECASE)
    if not citations:
        print("No citation found in answer")
        return

    # Establish the mapping from `citation_id` to doc chunk and corresponding doc
    candidate_references: Dict[int, dict] = {}
    for retrieved_doc in retrieved_docs:
        candidate_references[retrieved_doc["citation_id"]] = {"chunk": None, "doc": retrieved_doc["doc"],
                                                              "citation_id": retrieved_doc["citation_id"]}
        for chunk in retrieved_doc["chunks"]:
            candidate_references[chunk["citation_id"]] = {"chunk": chunk, "doc": retrieved_doc["doc"],
                                                          "citation_id": chunk["citation_id"]}

    grouped_citations = {}
    for match in citations:
        citation_id = int(re.sub(r'[^0-9]', '', ''.join(match)))
        if citation_id in candidate_references:
            # Get the specific doc content based on citation_id
            # And determine whether it is a paragraph of the same doc, and perform group logic
            citation = candidate_references[citation_id]
            doc = citation["doc"]
            if citation["doc"]["doc_id"] in grouped_citations:
                grouped_citations[doc["doc_id"]]["citations"].append(citation)
            else:
                grouped_citations[doc["doc_id"]] = {"doc": doc, "citations": [citation]}

    print("Model Answer: \n", answer)
    print("Grouped citations by doc: \n", grouped_citations)


if __name__ == "__main__":
    answer = "answer [citation:1][citation:2], answer2 [citation:3], answer3 [citation:4][citation:5], answer4 [citation:6][citation:7]"
    retrieved_docs = [
        {
            "citation_id": 1,
            "doc": {
                "doc_id": 1000,
            },
            "chunks": [
                {"citation_id": 2},
                {"citation_id": 3}
            ]
        },
        {
            "citation_id": 4,
            "doc": {
                "doc_id": 1001,
            },
            "chunks": [
                {"citation_id": 5}
            ]
        },
        {
            "citation_id": 6,
            "doc": {
                "doc_id": 1002,
            },
            "chunks": [
                {"citation_id": 7},
                {"citation_id": 8},
                {"citation_id": 9},
            ]
        },
    ]
    process_answer_references(answer, retrieved_docs)
