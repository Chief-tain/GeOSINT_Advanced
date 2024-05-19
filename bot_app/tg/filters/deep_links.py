import binascii
from dataclasses import replace
from typing import Optional

from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.deep_linking import decode_payload
from aiogram.filters.command import CommandException
from magic_filter import MagicFilter


class StrictDeeplink(CommandStart):
    def __init__(
        self,
        deep_link: bool,
        deep_link_encoded: bool,
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: Optional[MagicFilter] = None,
    ):
        super().__init__(
            deep_link=deep_link,
            deep_link_encoded=deep_link_encoded,
            ignore_case=ignore_case,
            ignore_mention=ignore_mention,
            magic=magic
        )

    def validate_deeplink(self, command: CommandObject) -> CommandObject:
        if not self.deep_link and command.args:
            raise CommandException("Deep-link was present")
        if not self.deep_link:
            return command
        if not command.args:
            raise CommandException("Deep-link was missing")
        args = command.args
        if self.deep_link_encoded:
            try:
                args = decode_payload(args)
            except (UnicodeDecodeError, binascii.Error) as e:
                raise CommandException(f"Failed to decode Base64: {e}")
            return replace(command, args=args)
        else:
            try:
                decode_payload(args)
            except (UnicodeDecodeError, binascii.Error):
                return command
            raise CommandException(f"Deeplink was encoded")
