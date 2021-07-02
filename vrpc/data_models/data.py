# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: seek_info.proto, function_types.proto, object_info_with_images.proto
# plugin: python-betterproto
from dataclasses import dataclass

import betterproto


class FunctionTypesEnum(betterproto.Enum):
    Unknown = 0
    Finish = 1
    Data = 2
    Start = 3
    Load = 4
    GetResult = 5
    Stop = 6


@dataclass
class SeekInfo(betterproto.Message):
    offset: int = betterproto.int32_field(1)


@dataclass
class FunctionTypes(betterproto.Message):
    function_types: "FunctionTypesEnum" = betterproto.enum_field(1)


@dataclass
class ObjectInfo(betterproto.Message):
    record_id: int = betterproto.int32_field(1)
    object_id: int = betterproto.int32_field(2)