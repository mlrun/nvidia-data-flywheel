from datetime import datetime
from src.lib.integration.record_exporter import RecordExporter
from src.lib.flywheel.util import identify_workload_type
from src.lib.integration.dataset_creator import DatasetCreator
from src.log_utils import setup_logging
from src.api.db_manager import TaskDBManager
from src.api.models import FlywheelRun, TaskResult
import mlrun

db_manager = TaskDBManager()
logger = setup_logging("create_dataset")


def create_dataset(
    context: mlrun.MLClientCtx,
    workload_id: str,
    client_id: str,
    output_dataset_prefix: str = "",
):
    flywheel_run = FlywheelRun(
        workload_id=workload_id,
        client_id=client_id,
        started_at=datetime.utcnow(),
        num_records=0,  # Will be updated when datasets are created
        nims=[],
    )
    flywheel_run_id = flywheel_run.id
    try:
        records = RecordExporter().get_records(client_id, workload_id)

        workload_type = identify_workload_type(records)

        datasets = DatasetCreator(
            records, flywheel_run_id, output_dataset_prefix, workload_id
        ).create_datasets()

        return {
            "workload_id": workload_id,
            "flywheel_run_id": str(flywheel_run_id),
            "client_id": client_id,
            "workload_type": workload_type,
            "datasets": datasets,
        }

    except Exception as e:
        error_msg = f"Error creating datasets: {e!s}"
        logger.error(error_msg)
        # Update flywheel run with error via the DB manager
        db_manager.mark_flywheel_run_error(flywheel_run_id, error_msg)
        # Return a TaskResult so that downstream tasks can gracefully short-circuit
        raise e
