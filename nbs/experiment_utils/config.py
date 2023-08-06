import dataclasses
import dataclasses_json

@dataclasses_json.dataclass_json
@dataclasses.dataclass
class InferenceConfig:
    mlflow_artifact_run_id: str
    triton_model_name: str
    triton_url: str
    score_threshold: float
