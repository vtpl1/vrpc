import logging
import os
import threading
import time
import uuid
from typing import Any, Union

LOGGER = logging.getLogger(__name__)


def ignore_exception(IgnoreException=Exception, DefaultVal=None):
    """Decorator for ignoring exception from a function
    e.g.   @ignore_exception(DivideByZero)
    e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
    """
    def dec(function):
        def _dec(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except IgnoreException:
                return DefaultVal

        return _dec

    return dec


get_int = ignore_exception(ValueError, 0)(int)


def get_folder_name(sub_folder: str) -> str:
    session_folder = os.path.join(os.getcwd(), sub_folder)
    return session_folder + os.path.sep


def get_folder(sub_folder: str) -> str:
    session_folder = get_folder_name(sub_folder)
    if not os.path.exists(session_folder):
        try:
            os.makedirs(session_folder)
            LOGGER.info(f"{sub_folder} folder created in {session_folder}")
        except OSError as e:
            LOGGER.error(e)
            # raise
    return session_folder


def get_queue_base_folder():
    return get_folder_name("session")
    #return "/session/"


def get_str_id(id: Union[int, str]) -> str:
    remove_characters = ["_", ".", "/", "\\", ",", ":", ";"]
    for r in remove_characters:
        id = id.replace(r, "-")

    if isinstance(id, int):
        return f"{id:05d}"
    elif isinstance(id, str):
        pass

    return id


def get_q_id(queue_id: Union[int, str]) -> str:
    return get_str_id(queue_id)


def get_channel_id(queue_id: Union[int, str]) -> str:
    return get_str_id(queue_id)


def get_q_folder(queue_id: str) -> str:
    return os.path.join(get_queue_base_folder(), queue_id)


def get_folder(sub_folder: str) -> str:
    session_folder = os.path.join(os.getcwd(), sub_folder)
    if not os.path.exists(session_folder):
        try:
            os.makedirs(session_folder)
            print("{} folder created in {}".format(sub_folder, session_folder))
        except OSError as e:
            print(e)
            # raise
    return session_folder + os.path.sep


channel_id: int = 0
channel_id_lock: threading.Lock = threading.Lock()


def get_channel_id() -> int:
    global channel_id
    channel_id += 1
    channel_id = channel_id % 30000
    return channel_id


def get_folder_dont_create(sub_folder: str) -> str:
    session_folder = os.path.join(os.getcwd(), sub_folder)
    if not os.path.exists(session_folder):
        pass
    return session_folder + os.path.sep


def get_package_folder(sub_folder: str) -> str:
    f = os.path.join(os.path.join(os.path.dirname(__file__), ".."), sub_folder)
    return f


def get_apps_summary_name() -> str:
    return get_session_folder() + "avaliable_apps.md"


def get_channels_summary_name() -> str:
    return get_session_folder() + "channels_summary.md"


def get_gpu_summary_name() -> str:
    return get_session_folder() + "gpu_summary.md"


def get_analytics_view_summary_name() -> str:
    return get_session_folder() + "analytics_view_summary.md"


def get_va_session_name() -> str:
    return get_session_folder() + "va_session"


def get_va_session_yaml_name() -> str:
    return get_session_folder() + "va_session.yaml"


def get_va_session_override_yaml_name() -> str:
    return get_session_folder() + "va_session_override.yaml"


def get_va_session_focus_yaml_name() -> str:
    return get_session_folder() + "va_session_focus.yaml"


def get_va_session_running_yaml_name() -> str:
    return get_session_folder() + "va_session_running.yaml"


def get_channel_wise_apps_name() -> str:
    return get_session_folder() + "channel_wise_apps.md"


def get_app_wise_channels_name() -> str:
    return get_session_folder() + "app_wise_channels.md"


def get_session_yaml_folder() -> str:
    return get_folder("override")


def get_session_folder() -> str:
    return get_folder("session")


def get_session_folder_name() -> str:
    return get_folder_name("session")


def get_app_folder() -> str:
    return get_folder("app")


def get_job_completion_folder() -> str:
    return get_folder("completed_jobs")


def get_downloads_folder() -> str:
    return get_folder("downloads")


def get_dump_folder() -> str:
    return get_folder("resLoc")


def get_events_image_folder() -> str:
    return get_folder(os.path.join(get_session_folder(), "events"))


def get_progress_folder() -> str:
    return get_session_folder()


def get_data_folder() -> str:
    return get_folder("persistent")


def get_images_folder() -> str:
    return get_package_folder("images")


def get_config_folder() -> str:
    return get_session_folder()


def get_temp_file_name() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def get_final_file_name(initial_file_name: str) -> str:
    return initial_file_name + "_" + time.strftime("%Y%m%d-%H%M%S")


def get_models_folder() -> str:
    return get_folder("models")


def get_generated_engines_folder() -> str:
    return get_folder("engines")


def get_dump_images() -> str:
    return get_folder("events")


id_generator = 0
id_generator_lock = threading.Lock()


def get_id() -> int:
    global id_generator, id_generator_lock
    with id_generator_lock:

        id_generator += 1
        return id_generator


def get_uuid_id() -> str:
    return str(uuid.uuid4())


def get_current_time() -> int:
    return int(round(time.time() * 1000))


def get_current_time_sec() -> int:
    return int(round(time.time()))


def change_from_nake_case_to_camel_case(in_str: str) -> str:
    # saving first and rest using split()
    init, *temp = in_str.split("_")
    # using map() to get all words other than 1st
    # and titlecasing them
    return "".join([init.lower(), *map(str.title, temp)])


def change_from_camel_case_to_snake_case(in_str: str) -> str:
    return "".join(["_" + i.lower() if i.isupper() else i for i in in_str]).lstrip("_")


def struct_to_dict(struct: Any) -> Any:
    result = {}

    # print struct
    def get_value(value: Any) -> Any:
        if (type(value) not in [int, float, bool]) and not bool(value):
            # it's a null pointer
            value = None
        elif type(value) is bytes and len(value) > 0:
            value = value.decode("utf-8")
        elif hasattr(value, "_length_") and hasattr(value, "_type_"):
            # Probably an array
            # print value
            value = get_array(value)
        elif hasattr(value, "_fields_"):
            # Probably another struct
            value = struct_to_dict(value)
        return value

    def get_array(array: Any) -> Any:
        ar = []
        for value in array:
            value = get_value(value)
            ar.append(value)
        return ar

    for field_name, _ in struct._fields_:
        value = getattr(struct, field_name)
        # if the type is not a primitive and it evaluates to False ...
        value = get_value(value)
        result[change_from_camel_case_to_snake_case(field_name)] = value
    return result
