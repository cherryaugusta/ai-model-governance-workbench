from celery import shared_task

from .services import evaluate_eval_run


@shared_task(name="evals.evaluate_eval_run_task")
def evaluate_eval_run_task(eval_run_id: int, correlation_id: str = "") -> int:
    run = evaluate_eval_run(eval_run_id=eval_run_id, correlation_id=correlation_id)
    return run.id
