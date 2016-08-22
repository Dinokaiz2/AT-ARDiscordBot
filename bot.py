import discord

class ATAR(discord.Client):
    def __init__(self):
        super.__init__()


    async def safe_send_message(self, dest, content, *, tts=False, expire_in=0, also_delete=None, quiet=False):
        msg = None
        try:
            msg = await self.send_message(dest, content, tts=tts)

            if msg and expire_in:
                asyncio.ensure_future(self._wait_delete_msg(msg, expire_in))

            if also_delete and isinstance(also_delete, discord.Message):
                asyncio.ensure_future(self._wait_delete_msg(also_delete, expire_in))

        except discord.Forbidden:
            if not quiet:
                self.safe_print("No permission to send message to %s" % dest.name)

        except discord.NotFound:
            if not quiet:
                self.safe_print("Unable to send message to %s" % dest.name)

        return msg
