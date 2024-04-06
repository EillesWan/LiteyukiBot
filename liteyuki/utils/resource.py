import json
import os
import shutil
from typing import Any

import nonebot
import yaml

from .data import LiteModel
from .language import get_default_lang

_loaded_resource_packs: list["ResourceMetadata"] = []  # 按照加载顺序排序
temp_resource_root = "data/liteyuki/resources"
lang = get_default_lang()


class ResourceMetadata(LiteModel):
    name: str = "Unknown"
    version: str = "0.0.1"
    description: str = "Unknown"
    path: str = ""
    folder: str = ""


def load_resource_from_dir(path: str):
    """
    把资源包按照文件相对路径复制到运行临时文件夹data/liteyuki/resources
    Args:
        path:  资源文件夹
    Returns:
    """
    if os.path.exists(os.path.join(path, "metadata.yml")):
        with open(os.path.join(path, "metadata.yml"), "r", encoding="utf-8") as f:
            metadata = yaml.safe_load(f)
    else:
        # 没有metadata.yml文件，不是一个资源包
        return
    for root, dirs, files in os.walk(path):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), path)
            copy_file(os.path.join(root, file), os.path.join(temp_resource_root, relative_path))
    metadata["path"] = path
    metadata["folder"] = os.path.basename(path)
    if os.path.exists(os.path.join(path, "lang")):
        from liteyuki.utils.language import load_from_dir
        load_from_dir(os.path.join(path, "lang"))
    _loaded_resource_packs.insert(0, ResourceMetadata(**metadata))


def get_path(path: str, abs_path: bool = False, default: Any = None) -> str | Any:
    """
    获取资源包中的文件
    Args:
        abs_path: 是否返回绝对路径
        default: 默认
        path: 文件相对路径
    Returns: 文件绝对路径
    """
    resource_relative_path = os.path.join(temp_resource_root, path)
    if os.path.exists(resource_relative_path):
        return os.path.abspath(resource_relative_path) if abs_path else resource_relative_path
    else:
        return default


def get_files(path: str, abs_path: bool = False) -> list[str]:
    """
    获取资源包中一个文件夹的所有文件
    Args:
        abs_path:
        path: 文件夹相对路径
    Returns: 文件绝对路径
    """
    resource_relative_path = os.path.join(temp_resource_root, path)
    if os.path.exists(resource_relative_path):
        return [os.path.abspath(os.path.join(resource_relative_path, file)) if abs_path else os.path.join(resource_relative_path, file) for file in
                os.listdir(resource_relative_path)]
    else:
        return []


def get_loaded_resource_packs() -> list[ResourceMetadata]:
    """
    获取已加载的资源包，优先级从前到后
    Returns: 资源包列表
    """
    return _loaded_resource_packs


def copy_file(src, dst):
    # 获取目标文件的目录
    dst_dir = os.path.dirname(dst)
    # 如果目标目录不存在，创建它
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    # 复制文件
    shutil.copy(src, dst)


def load_resources():
    """用于外部主程序调用的资源加载函数
    Returns:
    """
    # 加载默认资源和语言
    # 清空临时资源包路径data/liteyuki/resources
    _loaded_resource_packs.clear()
    if os.path.exists(temp_resource_root):
        shutil.rmtree(temp_resource_root)
    os.makedirs(temp_resource_root, exist_ok=True)

    standard_resource_path = "liteyuki/resources"
    load_resource_from_dir(standard_resource_path)
    # 加载其他资源包

    if not os.path.exists("resources"):
        os.makedirs("resources", exist_ok=True)

    if not os.path.exists("resources/index.json"):
        json.dump([], open("resources/index.json", "w", encoding="utf-8"))

    resource_index: list[str] = json.load(open("resources/index.json", "r", encoding="utf-8"))
    resource_index.reverse()    # 优先级高的后加载，但是排在前面
    for resource in resource_index:
        load_resource_from_dir(os.path.join("resources", resource))


def check_status(name: str) -> bool:
    """
    检查资源包是否已加载
    Args:
        name: 资源包名称，文件夹名
    Returns: 是否已加载
    """
    return name in [rp.folder for rp in get_loaded_resource_packs()]


def check_exist(name: str) -> bool:
    """
    检查资源包文件夹是否存在于resources文件夹
    Args:
        name: 资源包名称，文件夹名
    Returns: 是否存在
    """
    return os.path.exists(os.path.join("resources", name, "metadata.yml"))


def add_resource_pack(name: str) -> bool:
    """
    添加资源包，该操作仅修改index.json文件，不会加载资源包，要生效请重载资源
    Args:
        name: 资源包名称，文件夹名
    Returns:
    """
    if check_exist(name):
        old_index: list[str] = json.load(open("resources/index.json", "r", encoding="utf-8"))
        if name not in old_index:
            old_index.append(name)
            json.dump(old_index, open("resources/index.json", "w", encoding="utf-8"))
            load_resource_from_dir(os.path.join("resources", name))
            return True
        else:
            nonebot.logger.warning(lang.get("liteyuki.resource_loaded", name=name))
            return False
    else:
        nonebot.logger.warning(lang.get("liteyuki.resource_not_exist", name=name))
        return False


def remove_resource_pack(name: str) -> bool:
    """
    移除资源包，该操作仅修改加载索引，要生效请重载资源
    Args:
        name: 资源包名称，文件夹名
    Returns:
    """
    if check_exist(name):
        old_index: list[str] = json.load(open("resources/index.json", "r", encoding="utf-8"))
        if name in old_index:
            old_index.remove(name)
            json.dump(old_index, open("resources/index.json", "w", encoding="utf-8"))
            return True
        else:
            nonebot.logger.warning(lang.get("liteyuki.resource_not_loaded", name=name))
            return False
    else:
        nonebot.logger.warning(lang.get("liteyuki.resource_not_exist", name=name))
        return False


def change_priority(name: str, delta: int) -> bool:
    """
    修改资源包优先级
    Args:
        name: 资源包名称，文件夹名
        delta: 优先级变化，正数表示后移，负数表示前移，0表示移到最前
    Returns:
    """
    # 正数表示前移，负数表示后移
    old_resource_list: list[str] = json.load(open("resources/index.json", "r", encoding="utf-8"))
    new_resource_list = old_resource_list.copy()
    if name in old_resource_list:
        index = old_resource_list.index(name)
        if 0 <= index + delta < len(old_resource_list):
            new_index = index + delta
            new_resource_list.remove(name)
            new_resource_list.insert(new_index, name)
            json.dump(new_resource_list, open("resources/index.json", "w", encoding="utf-8"))
            return True
        else:
            nonebot.logger.warning("Priority change failed, out of range")
            return False
    else:
        nonebot.logger.debug("Priority change failed, resource not loaded")
        return False


def get_resource_metadata(name: str) -> ResourceMetadata:
    """
    获取资源包元数据
    Args:
        name: 资源包名称，文件夹名
    Returns:
    """
    for rp in get_loaded_resource_packs():
        if rp.folder == name:
            return rp
    return ResourceMetadata()
