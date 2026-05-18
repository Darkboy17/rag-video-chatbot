from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    '''
    Settings for the Social Video RAG .
    '''
    
    app_name: str = "Social Video RAG API"                      # The name of the app
    app_env: str = "development"                                # "development", "production", "testing"
    app_debug: bool = True                                      # Whether to run in debug mode
    
    frontend_origin: str = "http://localhost:3000"              # Used for CORS
    
    groq_api_key: str                                           # used by Groq for API calls
    models: list[str] = \
    ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]         # Models available for this project
    groq_model: str = models[1]                                 # the model to use for Groq
    groq_transcription_model: str = "whisper-large-v3-turbo"    # the model to use for transcription
    groq_trust_env: bool = False                                # whether to trust environment variables
    
    transcription_provider: str = "auto"                        # "auto", "local", "groq" - which transcription provider to use
    local_whisper_model: str = "base"                           # "tiny", "base", "small", "medium", "large"
    local_whisper_device: str = "cpu"                           # "cpu", "cuda", "npu"
    local_whisper_compute_type: str = "int8"                    # "int8", "float16", "float32"
    
    embedding_model: str = "BAAI/bge-small-en-v1.5"             # The model to use for embeddings - which is taken from Hugging Face Hub
    
    chroma_dir: str = "storage/chroma"                          # The directory to store the vector DB
    chroma_collection: str = "social_video_chunks"              # The name of the vector DB
    download_dir: str = "storage/downloads"                     # The directory to store downloaded files

    chunk_size: int = 900                                       # How many tokens per chunk, where a token could be a word or a character or a sentence
    chunk_overlap: int = 150                                    # How many tokens to overlap between chunks? -- too much overlap can cause the model to hallucinate 
                                                                # and too little overlap can cause the model to miss important information
    retrieval_k: int = 6                                        # How many chunks to retrieve from the vector DB

    ytdlp_cookies_from_browser: str | None = None               # The name of the browser to use for cookies
    ytdlp_js_runtime: str | None = "auto"                       # "auto", "deno", "node", "bun", "qjs"
    ytdlp_js_runtime_path: str | None = None                    # The path to the JS runtime
    ytdlp_remote_components: str | None = None                  # The path to the remote components
    ytdlp_no_check_certificate: bool = False                    # Whether to ignore SSL certificate errors
    ytdlp_socket_timeout: float | None = 60.0                   # used by ytdlp for socket timeout in seconds

    # Pydantic settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get the settings for the app.
    """
    return Settings()
