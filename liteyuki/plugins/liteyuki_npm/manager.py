import os

import nonebot.plugin
from nonebot import require
from nonebot.exception import FinishedException, IgnoredException
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.message import run_preprocessor
from nonebot.permission import SUPERUSER
from nonebot.plugin import Plugin

from liteyuki.utils.data_manager import GlobalPlugin, Group, InstalledPlugin, User, group_db, plugin_db, user_db
from liteyuki.utils.language import get_user_lang
from liteyuki.utils.ly_typing import T_Bot, T_MessageEvent
from liteyuki.utils.message import Markdown as md
from liteyuki.utils.permission import GROUP_ADMIN, GROUP_OWNER
from .common import get_plugin_can_be_toggle, get_plugin_default_enable, get_plugin_global_enable, get_plugin_session_enable
from .installer import get_store_plugin, npm_update
from ...utils.tools import clamp

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import on_alconna, Alconna, Args, Arparma, Subcommand

list_plugins = on_alconna(
    Alconna(
        "list-plugin",
        Args["page", int, 1]["num", int, 10],
    ),
    aliases={"列出插件", "插件列表"}
)

npm = on_alconna(
    aliases={"插件管理"},
    command=Alconna(
        "npm",
        # Args["plugin_name", str],
        Subcommand(
            "enable",
            Args["plugin_name", str],
            alias=["启用"],

        ),
        Subcommand(
            "disable",
            Args["plugin_name", str],
            alias=["停用"],
        ),
        Subcommand(
            "global-enable",
            Args["plugin_name", str],
            alias=["全局启用"],
        ),
        Subcommand(
            "global-disable",
            Args["plugin_name", str],
            alias=["全局停用"],
        ),
    ),

)


@list_plugins.handle()
async def _(event: T_MessageEvent, bot: T_Bot, result: Arparma):
    ulang = get_user_lang(str(event.user_id))
    if not os.path.exists("data/liteyuki/plugins.json"):
        await npm_update()

    loaded_plugin_list = sorted(nonebot.get_loaded_plugins(), key=lambda x: x.module_name)
    num_per_page = result.args.get("num")
    total = len(loaded_plugin_list) // num_per_page + (1 if len(loaded_plugin_list) % num_per_page else 0)

    page = clamp(result.args.get("page"), 1, total)

    # 已加载插件 | 总计10 | 第1/3页
    reply = (f"# {ulang.get('npm.loaded_plugins')} | "
             f"{ulang.get('npm.total', TOTAL=len(nonebot.get_loaded_plugins()))} | "
             f"{ulang.get('npm.page', PAGE=page, TOTAL=total)} \n***\n")

    for plugin in loaded_plugin_list[(page - 1) * num_per_page: min(page * num_per_page, len(loaded_plugin_list))]:
        # 检查是否有 metadata 属性
        # 添加帮助按钮
        btn_usage = md.btn_cmd(ulang.get("npm.usage"), f"help {plugin.module_name}", False)
        store_plugin = await get_store_plugin(plugin.module_name)
        session_enable = get_plugin_session_enable(event, plugin.module_name)
        if store_plugin:
            btn_homepage = md.btn_link(ulang.get("npm.homepage"), store_plugin.homepage)
            show_name = store_plugin.name
        elif plugin.metadata:
            if plugin.metadata.extra.get("liteyuki"):
                btn_homepage = md.btn_link(ulang.get("npm.homepage"), "https://github.com/snowykami/LiteyukiBot")
            else:
                btn_homepage = ulang.get("npm.homepage")
            show_name = plugin.metadata.name
        else:
            btn_homepage = ulang.get("npm.homepage")
            show_name = plugin.name
            ulang.get("npm.no_description")

        if plugin.metadata:
            reply += f"\n**{md.escape(show_name)}**\n"
        else:
            reply += f"**{md.escape(show_name)}**\n"

        reply += f"\n > {btn_usage}  {btn_homepage}"

        if await GROUP_ADMIN(bot, event) or await GROUP_OWNER(bot, event) or await SUPERUSER(bot, event):
            # 添加启用/停用插件按钮
            cmd_toggle = f"npm {'disable' if session_enable else 'enable'} {plugin.module_name}"
            text_toggle = ulang.get("npm.disable" if session_enable else "npm.enable")
            can_be_toggle = get_plugin_can_be_toggle(plugin.module_name)
            btn_toggle = text_toggle if not can_be_toggle else md.btn_cmd(text_toggle, cmd_toggle)
            reply += f"  {btn_toggle}"

            if await SUPERUSER(bot, event):
                plugin_in_database = plugin_db.first(InstalledPlugin(), "module_name = ?", plugin.module_name)
                # 添加移除插件和全局切换按钮
                global_enable = get_plugin_global_enable(plugin.module_name)
                btn_uninstall = (
                        md.btn_cmd(ulang.get("npm.uninstall"), f'npm uninstall {plugin.module_name}')) if plugin_in_database else ulang.get(
                    'npm.uninstall')
                btn_toggle_global_text = ulang.get("npm.disable_global" if global_enable else "npm.enable_global")
                cmd_toggle_global = f"npm {'global-disable' if global_enable else 'global-enable'} {plugin.module_name}"
                btn_toggle_global = btn_toggle_global_text if not can_be_toggle else md.btn_cmd(btn_toggle_global_text, cmd_toggle_global)

                reply += f"  {btn_uninstall}  {btn_toggle_global}"
        reply += "\n\n***\n"
    await md.send_md(reply, bot, event=event)


@npm.handle()
async def _(result: Arparma, event: T_MessageEvent, bot: T_Bot):
    if not os.path.exists("data/liteyuki/plugins.json"):
        await npm_update()
    # 判断会话类型
    ulang = get_user_lang(str(event.user_id))
    plugin_module_name = result.args.get("plugin_name")
    # 支持对自定义command_start的判断
    if result.subcommands.get("enable") or result.subcommands.get("disable"):

        toggle = result.subcommands.get("enable") is not None

        session_enable = get_plugin_session_enable(event, plugin_module_name)  # 获取插件当前状态

        default_enable = get_plugin_default_enable(plugin_module_name)  # 获取插件默认状态

        can_be_toggled = get_plugin_can_be_toggle(plugin_module_name)  # 获取插件是否可以被启用/停用

        if not can_be_toggled:
            await npm.finish(ulang.get("npm.plugin_cannot_be_toggled", NAME=plugin_module_name))

        if session_enable == toggle:
            await npm.finish(
                ulang.get("npm.plugin_already", NAME=plugin_module_name, STATUS=ulang.get("npm.enable") if toggle else ulang.get("npm.disable")))

        if event.message_type == "private":
            session = user_db.first(User(), "user_id = ?", event.user_id, default=User(user_id=event.user_id))
        else:
            if await GROUP_ADMIN(bot, event) or await GROUP_OWNER(bot, event) or await SUPERUSER(bot, event):
                session = group_db.first(Group(), "group_id = ?", event.group_id, default=Group(group_id=str(event.group_id)))
            else:
                raise FinishedException(ulang.get("Permission Denied"))
        try:
            if toggle:
                if default_enable:
                    session.disabled_plugins.remove(plugin_module_name)
                else:
                    session.enabled_plugins.append(plugin_module_name)
            else:
                if default_enable:
                    session.disabled_plugins.append(plugin_module_name)
                else:
                    session.enabled_plugins.remove(plugin_module_name)
            if event.message_type == "private":
                user_db.upsert(session)
            else:
                group_db.upsert(session)
        except Exception as e:
            print(e)
            await npm.finish(
                ulang.get(
                    "npm.toggle_failed",
                    NAME=plugin_module_name,
                    STATUS=ulang.get("npm.enable") if toggle else ulang.get("npm.disable"),
                    ERROR=str(e))
            )

        await npm.finish(
            ulang.get(
                "npm.toggle_success",
                NAME=plugin_module_name,
                STATUS=ulang.get("npm.enable") if toggle else ulang.get("npm.disable"))
        )
    elif result.subcommands.get("global-enable") or result.subcommands.get("global-disable") and await SUPERUSER(bot, event):
        toggle = result.subcommands.get("global-enable") is not None
        can_be_toggled = get_plugin_can_be_toggle(plugin_module_name)
        if not can_be_toggled:
            await npm.finish(ulang.get("npm.plugin_cannot_be_toggled", NAME=plugin_module_name))

        global_enable = get_plugin_global_enable(plugin_module_name)
        if global_enable == toggle:
            await npm.finish(
                ulang.get("npm.plugin_already", NAME=plugin_module_name, STATUS=ulang.get("npm.enable") if toggle else ulang.get("npm.disable")))

        try:
            plugin = plugin_db.first(GlobalPlugin(), "module_name = ?", plugin_module_name, default=GlobalPlugin(module_name=plugin_module_name))
            if toggle:
                plugin.enabled = True
            else:
                plugin.enabled = False
            plugin_db.upsert(plugin)
        except Exception as e:
            print(e)
            await npm.finish(
                ulang.get(
                    "npm.toggle_failed",
                    NAME=plugin_module_name,
                    STATUS=ulang.get("npm.enable") if toggle else ulang.get("npm.disable"),
                    ERROR=str(e))
            )

        await npm.finish(
            ulang.get(
                "npm.toggle_success",
                NAME=plugin_module_name,
                STATUS=ulang.get("npm.enable") if toggle else ulang.get("npm.disable"))
        )


@run_preprocessor
async def pre_handle(event: Event, matcher: Matcher):
    plugin: Plugin = matcher.plugin
    plugin_global_enable = get_plugin_global_enable(plugin.module_name)
    if not plugin_global_enable:
        raise IgnoredException("Plugin disabled globally")
    if event.get_type() == "message":
        plugin_session_enable = get_plugin_session_enable(event, plugin.module_name)
        if not plugin_session_enable:
            raise IgnoredException("Plugin disabled in session")

# @Bot.on_calling_api
# async def _(bot: Bot, api: str, data: dict[str, any]):
#     nonebot.logger.info(f"Plugin Callapi: {api}: {data}")
