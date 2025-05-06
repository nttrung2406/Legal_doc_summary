# Broker settings
broker_url = 'amqp://localhost:5672//'
result_backend = 'rpc://'

# Task settings
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 50
worker_max_memory_per_child = 150000  # 150MB

# Task routing
task_routes = {
    'tasks.cleanup_old_documents': {'queue': 'cleanup'}
}

# Task time limits
task_time_limit = 3600  # 1 hour
task_soft_time_limit = 3000  # 50 minutes 