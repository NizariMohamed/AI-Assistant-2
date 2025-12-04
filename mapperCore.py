# mapperCore.py
from mapper import *


def execute_action(action: str, params: dict):

    # FILE SYSTEM
    if action == "list_dir":
        return action_list_dir(params["path"])
    elif action == "show_file":
        return action_show_file(params["path"])
    elif action == "create_file":
        return action_create_file(params["path"])
    elif action == "write_file":
        return action_write_file(params["path"], params["content"])
    elif action == "append_file":
        return action_append_file(params["path"], params["content"])
    elif action == "remove_file":
        return action_remove_file(params["path"])
    elif action == "move_file":
        return action_move_file(params["src"], params["dest"])
    elif action == "copy_file":
        return action_copy_file(params["src"], params["dest"])

    # SYSTEM INFO
    elif action == "get_system_info":
        return action_get_system_info()
    elif action == "get_cpu_usage":
        return action_get_cpu_usage()
    elif action == "get_memory_usage":
        return action_get_memory_usage()
    elif action == "get_disk_usage":
        return action_get_disk_usage(params["path"])

    # NETWORK
    elif action == "ping_host":
        return action_ping_host(params["host"])
    elif action == "download_file":
        return action_download_file(params["url"], params["save_path"])
    elif action == "open_url":
        return action_open_url(params["url"])

    # PROCESS
    elif action == "run_program":
        return action_run_program(params["command"], params.get("args", []))
    elif action == "kill_process":
        return action_kill_process(params["pid"])
    elif action == "start_service":
        return action_start_service(params["service"])
    elif action == "stop_service":
        return action_stop_service(params["service"])

    # TEXT UTILITIES
    elif action == "summarize_text":
        return action_summarize_text(params["text"])
    elif action == "extract_entities":
        return action_extract_entities(params["text"])
    elif action == "classify_text":
        return action_classify_text(params["text"], params["labels"])
    elif action == "plan_task":
        return action_plan_task(params["goal"])

    # MULTI ACTION
    elif action == "multi_action_plan":
        return action_multi_action_plan(execute_action, params["steps"])

    return "Unknown action"
