

## fix to prevent attr error in logger.addHandler
from logging import handlers

import contextlib
import logging
import os
import re
import sys

import discord.errors


class PIDManager(contextlib.ContextDecorator):

  def __init__(self, pidfile, on_exists_callback=None):
    self.on_exists_callback = on_exists_callback
    self._pidfile = None
    super().__init__()
    self.pidfile = pidfile

  @property
  def pidfile(self):
    return self._pidfile

  @pidfile.setter
  def pidfile(self, pidfile):
    if self._pidfile is not None:
      ## if the pidfile is changed for another location
      os.unlink(self.pidfile)
    self._pidfile = pidfile
    if self.pidfile is not None:
      pid = self.create_pid_file()
      if pid is not None and self.on_exists_callback is not None:
        self.on_exists_callback(pid)
        # raise RuntimeError(f"This bot is already running - pid: {pid}.")

  def create_pid_file(self):
    if os.path.exists(self.pidfile):
      with open(self.pidfile, 'r') as pidfile:
        return pidfile.read()
    with open(self.pidfile, 'w') as pidfile:
      pidfile.write(f"{os.getpid()}")
    return None

  def __enter__(self):
    pass

  def __exit__(self, *exc):
    if self.pidfile is not None:
      os.unlink(self.pidfile)



def get_formater():
  return logging.Formatter(
    "[%(name)-16s-%(levelname)-5s %(asctime)s] %(message)s",
    "%Y-%m-%d %H:%M:%S"
  )

def get_logger(name, filename=None, debug=False, noprint=True):
  logger = logging.getLogger(name)
  logger.setLevel(logging.DEBUG if debug else logging.INFO)

  formater = get_formater()

  if not noprint:
    add_stdout_handler(logger)

  if filename:
    try:
      file_stream_handler = logging.handlers.RotatingFileHandler(
        filename, maxBytes=10_000_000
      )
      file_stream_handler.setFormatter(formater)
      logger.addHandler(file_stream_handler)
    except AttributeError as e:
      pass
  return logger

def add_stdout_handler(logger):
  stream_handler = logging.StreamHandler(sys.stdout)
  stream_handler.setFormatter(get_formater())
  logger.addHandler(stream_handler)

async def user_from_mention(client, mention, logger=None, guild=None):
  if re.match(r"<@&\d{18}>", mention):
    return None
  match = re.search(r"\d{18}", mention)
  user_id = match[0]
  logger and logger.debug(f"Fetching user of ID {user_id}")
  if guild:
    return await guild.fetch_member(int(user_id))
  else:
    return await client.fetch_user(int(user_id))
