from datetime import datetime
from collections.abc import Callable

from src.api.db_manager import TaskDBManager
from src.api.models import TaskResult
from src.config import settings
from src.lib.nemo.dms_client import DMSClient
from src.log_utils import setup_logging
import mlrun

logger = setup_logging("data_flywheel.tasks")

# Centralised DB helper - keeps Mongo specifics out of individual tasks
db_manager = TaskDBManager()

def shutdown_deployment(
    context: mlrun.MLClientCtx,
    base_eval_result: dict,
    icl_eval_result: dict,
    customization_eval_result: dict,
) -> dict:
    previous_results = [
        base_eval_result,
        icl_eval_result,
        customization_eval_result,
    ]
    previous_result: TaskResult | None = None
    try:
        previous_result = _extract_previous_result(
            previous_results,
            validator=lambda r: getattr(r, "nim", None) is not None,
            error_msg="No valid TaskResult with NIM config found in results",
        )
        if (
            previous_result.llm_judge_config
            and previous_result.llm_judge_config.model_name == previous_result.nim.model_name
        ):
            logger.info(
                f"Skip shutting down NIM {previous_result.nim.model_name} as it is the same as the LLM Judge"
            )
            return previous_result.model_dump(mode="json")

        logger.info(f"Shutting down NIM {previous_result.nim.model_name} in {settings.nmp_config.nmp_namespace} namespace")
        dms_client = DMSClient(nmp_config=settings.nmp_config, nim=previous_result.nim)
        dms_client.shutdown_deployment()

        # Mark the NIM run as completed now that the deployment is shut down
        try:
            nim_run_doc = db_manager.find_nim_run(
                previous_result.flywheel_run_id,
                previous_result.nim.model_name,
            )
            if nim_run_doc:
                finished_time = datetime.utcnow()
                started_at = nim_run_doc.get("started_at")
                runtime_seconds: float = 0.0
                if started_at:
                    runtime_seconds = (finished_time - started_at).total_seconds()

                db_manager.mark_nim_completed(nim_run_doc["_id"], finished_time, runtime_seconds)
        except Exception as update_err:
            logger.error("Failed to update NIM run status to COMPLETED: %s", update_err)

        return previous_result.model_dump(mode="json")
    except Exception as e:
        error_msg = f"Error shutting down NIM deployment: {e!s}"
        logger.error(error_msg)

        # ``previous_result`` may not be available if extraction failed.
        previous_result = locals().get("previous_result")  # type: ignore[arg-type]
        if not previous_result:
            return previous_result.model_dump(mode="json")  # type: ignore[return-value]

        nim_run_doc = db_manager.find_nim_run(
            previous_result.flywheel_run_id,
            previous_result.nim.model_name,
        )
        if not nim_run_doc:
            logger.error(
                f"Could not find NIM run for flywheel_run_id: {previous_result.flywheel_run_id}"
            )
            return previous_result.model_dump(mode="json")

        # Update nim document with error
        db_manager.mark_nim_error(nim_run_doc["_id"], error_msg)
        previous_result.error = error_msg
    return previous_result.model_dump(mode="json")

def _extract_previous_result(
    previous_results: list[TaskResult] | TaskResult | dict,
    *,
    validator: Callable[[TaskResult], bool] | None = None,
    error_msg: str = "No valid TaskResult found",
) -> TaskResult:
    # Fast-path: a single object (TaskResult or dict)
    if not isinstance(previous_results, list):
        if isinstance(previous_results, dict):
            return TaskResult(**previous_results)
        assert isinstance(previous_results, TaskResult)
        return previous_results

    # It is a list - iterate from the end (latest first)
    for result in reversed(previous_results):
        if isinstance(result, dict):
            result = TaskResult(**result)
        if not isinstance(result, TaskResult):
            continue
        if validator is None or validator(result):
            return result

    # Nothing matched - raise so caller can handle
    logger.error(error_msg)
    raise ValueError(error_msg)
