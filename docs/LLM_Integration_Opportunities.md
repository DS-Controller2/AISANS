# LLM Integration Opportunities in AIsans Project

## Introduction

This document outlines potential integration points for Large Language Models (LLMs) within the AIsans meta-search engine project. The goal is to identify areas where LLMs can enhance user experience, search result quality, and overall functionality. Each section details a specific opportunity, the relevant components, the potential LLM tasks, the benefits, and a high-level testing strategy.

---

### 1. Advanced Query Understanding and Expansion

*   **Component:** `aisans/metasearch/core.py` (specifically `enhance_query_llm` and potentially new functions)
*   **Potential LLM Task(s):**
    *   **Synonym Generation & Query Rephrasing:** (Partially implemented) Expand queries with relevant synonyms or alternative phrasings.
    *   **Intent Recognition:** Identify the underlying intent of the query (e.g., informational, navigational, transactional) to tailor the search strategy or result presentation.
    *   **Keyword Extraction & Prioritization:** Identify the most critical keywords in a query, especially for longer, more natural language queries.
    *   **Sub-query Generation:** For complex queries, break them down into multiple sub-queries that can be executed independently and their results merged.
*   **Benefit:**
    *   Improves search relevance by matching user intent more accurately.
    *   Increases the recall of relevant documents by considering variations of the query.
    *   Handles complex or ambiguous queries more effectively.
*   **High-Level Testing Strategy:**
    *   **Unit Tests (`tests/metasearch/test_core.py`):**
        *   Mock the `LLMClient.generate_text` or `LLMClient.generate_chat_completion` methods.
        *   Assert that the LLM is called with appropriately constructed prompts for each task (e.g., "Identify keywords in...", "Rephrase this query...", "What is the intent of...").
        *   Verify that the function correctly processes the LLM's response (e.g., extracts keywords, uses the rephrased query).
        *   Test fallback behavior: if the LLM fails or returns irrelevant output, the system should gracefully default to the original query or a safe modification.
    *   **Integration Tests (`scripts/run_metasearch.py` or new test scripts):**
        *   Provide a set of diverse test queries (simple, complex, ambiguous).
        *   If `OPENROUTER_API_KEY` is set, observe (manually or via logging) the LLM-modified queries and the impact on search results from live engines.
        *   Compare results for original vs. LLM-enhanced queries for a qualitative assessment.

---

### 2. Intelligent Snippet Generation during Indexing or Result Presentation

*   **Component:**
    *   `aisans/indexer/indexer.py` (if snippets are pre-generated and stored)
    *   `aisans/metasearch/core.py` or a new results presentation module (if snippets are generated on-the-fly from retrieved content).
*   **Potential LLM Task(s):**
    *   **Query-Aware Summarization:** Instead of a generic snippet (e.g., first N characters), generate a snippet from the document's body that is most relevant to the *user's query*.
    *   **Key Information Extraction:** Identify and extract key pieces of information from the document related to the query.
*   **Benefit:**
    *   Provides users with more informative and relevant snippets, helping them quickly assess if a search result is pertinent.
    *   Reduces the need for users to click through to pages that are not relevant.
*   **High-Level Testing Strategy:**
    *   **Unit Tests:**
        *   **For Indexer (if pre-generating):** In `tests/indexer/test_indexer.py`, when testing `add_document`. Mock `LLMClient`. Provide sample document content and a query. Assert that the LLM is called with a prompt asking for a query-aware summary of the content. Verify the generated snippet is stored correctly.
        *   **For On-the-fly Generation:** In `tests/metasearch/test_core.py` or a new test module. Mock `LLMClient`. Provide sample document content (e.g., from a mocked search engine result) and a user query. Assert LLM is called for summarization based on the query and content. Verify the snippet in the final search result.
        *   Test fallback: If LLM fails, a default snippet generation method (e.g., truncation) should be used.
    *   **Integration Tests:**
        *   Visually inspect search results for various queries to assess the quality and relevance of LLM-generated snippets compared to basic snippets.

---

### 3. Answer Synthesis from Multiple Search Results

*   **Component:** `aisans/metasearch/core.py` or a new module dedicated to result processing and answer generation.
*   **Potential LLM Task(s):**
    *   **Multi-Document Summarization & Synthesis:** After retrieving top N search results, pass their content (or relevant snippets/summaries) to an LLM.
    *   Ask the LLM to synthesize a direct answer to the user's query based on the provided information, potentially citing sources.
*   **Benefit:**
    *   Provides users with direct answers to informational queries, similar to "featured snippets" or "AI overviews" in major search engines.
    *   Saves users time by consolidating information from multiple sources.
*   **High-Level Testing Strategy:**
    *   **Unit Tests:**
        *   Mock `LLMClient.generate_chat_completion` (as this is more of a chat/instruction-following task).
        *   Create mock search results (list of dictionaries with 'title', 'url', 'snippet'/'body').
        *   Assert that the LLM is called with a prompt containing the information from these results and instructions to synthesize an answer for a given query.
        *   Verify how the synthesized answer is formatted and returned by the function.
        *   Test cases where results are insufficient or conflicting, and how the LLM (or the calling logic) handles this (e.g., "Could not synthesize a definitive answer...").
        *   Test fallback: If LLM fails or cannot generate an answer, the system should default to showing standard search results.
    *   **Integration Tests:**
        *   For a set of test queries (especially question-like queries), run the meta-search.
        *   If `OPENROUTER_API_KEY` is available, observe the synthesized answer presented above or alongside the standard results.
        *   Evaluate the factual accuracy, coherence, and relevance of the synthesized answer (this often requires human judgment).

---
