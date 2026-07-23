# Current Status and Implementation Plan

## 1. Current Status

### Completed stages
- PDF extraction has been completed and source documents are available in `AI-Legal-Chatbot/data/extracted_text`.
- Text cleaning pipeline is implemented in `AI-Legal-Chatbot/src/preprocessing/text_cleaner.py`.
- Section-wise chunking pipeline is implemented in `AI-Legal-Chatbot/src/preprocessing/chunk_generator.py`.
- Chunk metadata generation pipeline is implemented in `AI-Legal-Chatbot/src/preprocessing/metadata_generator.py`.
- The metadata output was rebuilt to a flat schema containing fields such as:
  - `chunk_id`, `law_name`, `law_short`, `year`
  - `chapter_number`, `chapter_title`, `section_number`, `section_title`
  - `legal_domain`, `document_type`, `language`
  - `keywords`, `entities`, `topics`
  - `contains_explanation`, `contains_proviso`, `contains_exception`, `contains_definition`
  - `cross_references`, `page_start`, `page_end`
- Repository hygiene was improved with a new `.gitignore` covering generated data, virtual environments, caches, logs, and vector DB artifacts.

### Current code and outputs
- `AI-Legal-Chatbot/src/preprocessing/` contains the ingestion pipeline.
- `AI-Legal-Chatbot/data/cleaned_text/` holds cleaned document outputs.
- `AI-Legal-Chatbot/data/chunks/` holds section-wise chunk files.
- `AI-Legal-Chatbot/data/metadata/` holds flat metadata JSON outputs.
- `AI-Legal-Chatbot/src/embedding/` contains the embedding generation skeleton.

### Status summary
- ✅ Data ingestion and preprocessing: complete.
- ✅ Metadata structure: flat, chunk-level, retrieval-ready.
- ⚠️ Embedding generation: implemented in code, but FAISS index creation must be validated and completed.
- ⚠️ Retrieval layer: not yet implemented end-to-end.
- ⚠️ Chatbot response engine: not yet implemented.
- ⚠️ Frontend UI and LLM integration: not yet implemented.

## 2. Short-term Implementation Plan

### A. Finalize embedding stage
- Implement and validate `load_chunks()` to read metadata and attach original chunk text.
- Use `BAAI/bge-large-en-v1.5` for embedding generation.
- Implement `generate_embeddings()` for batched encoding and normalized vectors.
- Build a FAISS index with `build_faiss_index()`.
- Save outputs to:
  - `AI-Legal-Chatbot/data/vector_db/legal_index.faiss`
  - `AI-Legal-Chatbot/data/vector_db/chunks_metadata.pkl`
- Add verification logic to confirm index file creation and retrieval correctness.

### B. Build retrieval layer
- Create a similarity search module in `AI-Legal-Chatbot/src/retrieval/`.
- Load FAISS index and metadata payload.
- Implement `search_similar_chunks(query, top_k=5)`.
- Add filters by law, chapter, section, or topic.
- Build a prompt assembly layer that formats retrieved chunks and metadata for the LLM.

### C. Implement RAG response engine
- Create `AI-Legal-Chatbot/src/llm/response_generator.py`.
- Use `AI-Legal-Chatbot/src/llm/ollama_client.py` or a local/cloud-compatible LLM interface.
- Include retrieved legal chunks, citation metadata, and user conversation history in prompt templates.
- Enforce answer grounding and legal disclaimer behavior.

## 3. Mid-term Implementation Plan

### D. Chatbot backend and conversation flow
- Create chatbot orchestration in `AI-Legal-Chatbot/src/chatbot/`.
- Implement:
  - conversation memory
  - follow-up question logic
  - intent classification
  - multi-turn context handling
- Ensure the backend returns both:
  - answer text
  - retrieval metadata and source references

### E. Frontend chatbot UI
- Build a UI for the chatbot, ideally starting with a lightweight framework.
- Recommended MVP options:
  - Streamlit for fastest prototype
  - React/Vite for production readiness
- UI features:
  - chat message list
  - user query input
  - source citations panel
  - session history
  - filter options by law or topic
  - conversation state display

### F. LLM integration and system prompts
- Implement a safe system prompt template.
- Add mechanisms to prevent hallucinations:
  - strict use of retrieved citations
  - refusal to provide legal advice
  - clarifying statements for ambiguous queries
- Support both local LLM deployment and remote API mode.

## 4. Long-term Implementation Plan

### G. Deployment and infrastructure
- Prepare deployment for backend and frontend.
- Add environment variable management for:
  - model selection
  - HF tokens or LLM keys
  - vector DB path
  - logging settings
- Consider Docker packaging for the full project.

### H. Testing, evaluation, and iteration
- Create test cases for legal query scenarios:
  - criminal procedure
  - evidence law
  - consumer protection
  - IT Act / cybercrime
  - traffic law
  - RTI and administrative transparency
- Validate retrieval relevance and answer grounding.
- Improve chunking or metadata generation if retrieval quality is weak.

## 5. Recommended Future Functions

### Core backend functions
- `load_chunks(metadata_dir, chunks_dir)`
- `load_embedding_model(model_name, device)`
- `generate_embeddings(records, model, batch_size)`
- `build_faiss_index(embeddings)`
- `save_index(index, records, output_dir)`
- `load_faiss_index(index_path)`
- `load_metadata_payload(metadata_path)`
- `search_similar_chunks(query, index, metadata, top_k)`
- `build_rag_prompt(query, retrieved_chunks, history)`
- `generate_response(prompt)`
- `get_answer_with_sources(query, history)`

### Chatbot conversation functions
- `create_or_resume_session(session_id)`
- `store_user_query(session_id, query)`
- `retrieve_context(session_id)`
- `ask_follow_up_question(session_id, missing_data)`
- `format_chat_response(answer, sources, next_steps)`

### Frontend functions / components
- `ChatWindow`
- `MessageInput`
- `ConversationHistory`
- `SourceReferencesPanel`
- `LegalMetadataCard`
- `SessionControls`
- `QueryFilterBar`

### LLM prompt and safety functions
- `build_system_prompt()`
- `build_retrieval_context_block(retrieved_chunks)`
- `enforce_response_style(answer)`
- `sanitize_user_input(query)`
- `apply_legal_disclaimer(answer)`

## 6. Complete Project Completion Checklist
- [x] PDF extraction
- [x] Text cleaning
- [x] Section-wise chunking
- [x] Flat metadata generation
- [ ] Embedding generation and FAISS indexing
- [ ] Retrieval module and semantic search
- [ ] RAG prompt construction
- [ ] LLM integration
- [ ] Backend chatbot orchestration
- [ ] Frontend chat UI
- [ ] Deployment packaging
- [ ] Testing and evaluation

## 7. Next Recommended Step
1. Validate the embedding pipeline end-to-end and save `legal_index.faiss` + `chunks_metadata.pkl`.
2. Implement the retrieval layer and confirm search results.
3. Build the RAG prompt flow and connect the backend to the LLM.
4. Add the frontend chatbot interface.
5. Test with real legal queries and iterate.
