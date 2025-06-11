from src.config import settings
from src.log_utils import setup_logging
from src.api.models import LLMJudgeRun, DeploymentStatus, TaskResult
from bson import ObjectId
from src.api.db_manager import TaskDBManager
from src.lib.nemo.dms_client import DMSClient
import mlrun

logger = setup_logging("wait_for_llm_as_judge")
db_manager = TaskDBManager()

def wait_for_llm_as_judge(context: mlrun.MLClientCtx, previous_result: dict):
    previous_result = TaskResult(**previous_result)
    judge_cfg = settings.llm_judge_config
    if judge_cfg.is_remote():
        logger.info("Remote LLM Judge will be used")
        previous_result.llm_judge_config = None
        return _prepare_output(previous_result)

    llm_judge_config = judge_cfg.get_local_nim_config()
    previous_result.llm_judge_config = llm_judge_config

    # Create LLM judge run using TaskDBManager
    llm_judge_run = LLMJudgeRun(
        flywheel_run_id=ObjectId(previous_result.flywheel_run_id),
        model_name=llm_judge_config.model_name,
    )

    # Insert using TaskDBManager
    llm_judge_run.id = db_manager.create_llm_judge_run(llm_judge_run)

    dms_client = DMSClient(nmp_config=settings.nmp_config, nim=llm_judge_config)

    def progress_callback(status: dict):
        db_manager.update_llm_judge_deployment_status(
            llm_judge_run.id,
            DeploymentStatus(status.get("status", "unknown")),
        )

    dms_client.wait_for_deployment(progress_callback=progress_callback)
    dms_client.wait_for_model_sync(llm_judge_config.target_model_for_evaluation())

    return _prepare_output(previous_result)

def _prepare_output(obj):
    # convert "None" to None:
    return {
    k: v if v != "None" else None
    for k, v in obj.model_dump().items()
}
