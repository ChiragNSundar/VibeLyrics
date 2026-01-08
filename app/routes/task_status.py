"""
Task Status Routes
Endpoints for checking async task status
"""
from flask import Blueprint, jsonify

task_status_bp = Blueprint('task_status', __name__)


@task_status_bp.route('/task/<task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """
    Get the status of an async task.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status and result if complete
    """
    from app.celery_app import celery_app
    
    result = celery_app.AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready()
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.get()
        else:
            response["error"] = str(result.result)
    
    return jsonify(response)


@task_status_bp.route('/task/<task_id>/result', methods=['GET'])
def get_task_result(task_id):
    """
    Get the result of a completed task.
    Blocks until task is complete (with timeout).
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task result
    """
    from app.celery_app import celery_app
    
    result = celery_app.AsyncResult(task_id)
    
    try:
        # Wait up to 30 seconds for result
        task_result = result.get(timeout=30)
        return jsonify({
            "task_id": task_id,
            "status": "SUCCESS",
            "result": task_result
        })
    except Exception as e:
        return jsonify({
            "task_id": task_id,
            "status": result.status,
            "error": str(e)
        }), 500


@task_status_bp.route('/task/<task_id>/revoke', methods=['POST'])
def revoke_task(task_id):
    """Cancel a pending task"""
    from app.celery_app import celery_app
    
    celery_app.control.revoke(task_id, terminate=True)
    
    return jsonify({
        "task_id": task_id,
        "status": "REVOKED",
        "message": "Task cancelled"
    })
