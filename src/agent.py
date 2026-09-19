from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Không tìm thấy thông tin trong cơ sở dữ liệu (knowledge store rỗng)."

        chunks = self.store.search(question, top_k=top_k)
        if not chunks:
            return "Không tìm thấy thông tin phù hợp trong tài liệu để trả lời câu hỏi."

        context_blocks = []
        for idx, chunk in enumerate(chunks, 1):
            source = (
                chunk.get("metadata", {}).get("source")
                or chunk.get("metadata", {}).get("doc_id")
                or chunk.get("id", "Unknown")
            )
            context_blocks.append(f"[{idx}] (Nguồn: {source})\n{chunk.get('content', '')}")
        context_text = "\n\n".join(context_blocks)

        prompt = (
            "Dựa vào các đoạn ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi.\n"
            "- Chỉ sử dụng thông tin có trong ngữ cảnh, không tự suy diễn hoặc bịa đặt ngoài ngữ cảnh.\n"
            "- Nếu ngữ cảnh không chứa đủ thông tin để trả lời, hãy nêu rõ là không tìm thấy thông tin.\n"
            "- Khi trả lời, hãy trích dẫn số thứ tự đoạn ngữ cảnh [1], [2]... tương ứng làm bằng chứng.\n\n"
            f"Ngữ cảnh:\n{context_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Câu trả lời:"
        )

        return self.llm_fn(prompt)
