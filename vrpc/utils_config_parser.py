from configparser import ConfigParser
from typing import Any, Optional


def put_config_value(
    config: ConfigParser,
    section_name: str,
    key_name: str,
    key_value: Any,
    key_comment: str = None,
) -> int:
    ret = 0

    key_name.replace("_", "-")
    comment_prefix = "# "
    if not config.has_section(section_name):
        config.add_section(section_name)
        config[section_name] = {}
        ret += 1

    if not config.has_option(section=section_name, option=key_name):
        if key_comment:
            config.set(section=section_name, option=comment_prefix + key_comment, value=None)
        config.set(section=section_name, option=key_name, value=str(key_value))
        ret += 1
    return ret


def has_option(config: ConfigParser, section_name: str, key_name: str) -> bool:
    key_name.replace("_", "-")
    return config.has_option(section_name, key_name)


def get_config_value(config: ConfigParser, section_name: str, key_name: str, default_value: Any) -> Any:
    ret: Optional[Any] = None
    key_name.replace("_", "-")
    if isinstance(default_value, bool):
        ret = config.getboolean(section_name, key_name, fallback=default_value)
    elif isinstance(default_value, int):
        ret = config.getint(section_name, key_name, fallback=default_value)
    elif isinstance(default_value, str):
        ret = config.get(section_name, key_name, fallback=default_value)
    else:
        raise Exception("Unknown value type")
    return ret
