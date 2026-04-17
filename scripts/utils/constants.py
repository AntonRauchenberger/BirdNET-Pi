from enum import Enum

class BenchmarkTimerNames(Enum):
    TOTAL_ANALYSIS = "total analysis"
    TOTAL_REPORTING = "total reporting"
    UPDATE_JSON_FILE = "update json file"
    UPDATE_DB_AND_FILE = "write to db and file"
    SERVER_POST = "soundscape POST to server"
    AUDIO_ANALYSIS = "audio analysis"
    INFERENCE = "inference"
    MODEL_LOADING = "model loading"
    AUDIO_PROCESSING = "audio processing"
    POST_PROCESSING_DETECTIONS = "post processing detections"

BENCHMARKING_SCENARIO = "Local Laptop Development"