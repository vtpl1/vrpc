# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: object_info_with_images.proto, opencv.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import List

import betterproto


@dataclass(eq=False, repr=False)
class OcvMat(betterproto.Message):
    rows: int = betterproto.int32_field(1)
    cols: int = betterproto.int32_field(2)
    mat_data_type: int = betterproto.int32_field(3)
    mat_data_size: int = betterproto.int32_field(4)
    mat_data: bytes = betterproto.bytes_field(5)

    __annotations__ = {
        "rows": int,
        "cols": int,
        "mat_data_type": int,
        "mat_data_size": int,
        "mat_data": bytes,
    }


@dataclass(eq=False, repr=False)
class Rect(betterproto.Message):
    left: int = betterproto.int32_field(1)
    top: int = betterproto.int32_field(2)
    width: int = betterproto.int32_field(3)
    height: int = betterproto.int32_field(4)

    __annotations__ = {
        "left": int,
        "top": int,
        "width": int,
        "height": int,
    }


@dataclass(eq=False, repr=False)
class ListRect(betterproto.Message):
    rect: List["Rect"] = betterproto.message_field(1)

    __annotations__ = {
        "rect": List["Rect"],
    }


@dataclass(eq=False, repr=False)
class ChannelDetails(betterproto.Message):
    my_id: str = betterproto.string_field(1)
    engine_name: str = betterproto.string_field(2)
    engine_type: str = betterproto.string_field(3)
    channel_name: str = betterproto.string_field(4)
    camera_ip: str = betterproto.string_field(5)
    latitude: float = betterproto.float_field(6)
    longitude: float = betterproto.float_field(7)

    __annotations__ = {
        "my_id": str,
        "engine_name": str,
        "engine_type": str,
        "channel_name": str,
        "camera_ip": str,
        "latitude": float,
        "longitude": float,
    }


@dataclass(eq=False, repr=False)
class ObjectInfo(betterproto.Message):
    message_id: int = betterproto.int32_field(1)
    face_rect: "Rect" = betterproto.message_field(2)
    gender: str = betterproto.string_field(3)
    race: str = betterproto.string_field(4)
    capture_resolution: int = betterproto.int32_field(5)
    capture_time: float = betterproto.float_field(6)
    auto_registration_tag: int = betterproto.int32_field(7)
    spoof_tag: bool = betterproto.bool_field(8)
    channel_details: "ChannelDetails" = betterproto.message_field(9)
    face_chip: "OcvMat" = betterproto.message_field(10)
    extended_face_chip: "OcvMat" = betterproto.message_field(11)
    full_image: "OcvMat" = betterproto.message_field(12)

    __annotations__ = {
        "message_id": int,
        "face_rect": "Rect",
        "gender": str,
        "race": str,
        "capture_resolution": int,
        "capture_time": float,
        "auto_registration_tag": int,
        "spoof_tag": bool,
        "channel_details": "ChannelDetails",
        "face_chip": "OcvMat",
        "extended_face_chip": "OcvMat",
        "full_image": "OcvMat",
    }
