from typing import Optional

import typer

import settings

import os

import logging
import sys

from __init__ import __app_name__, __version__

__name__ = __app_name__

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# this is just to make the output look nice
formatter = logging.Formatter(fmt="%(asctime)s %(name)s %(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")

# this logs to stdout and I think it is flushed immediately
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

from __init__ import __app_name__, __version__

app = typer.Typer()

def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return


@app.command()
def restart() -> None:
  """Restart the daemon service"""
  os.system("systemctl --user restart socksproxyman.service")

@app.command()
def stop() -> None:
  """Stop the daemon service"""
  os.system("systemctl --user stop socksproxyman.service")

@app.command()
def start() -> None:
  """Start the daemon service"""
  os.system("systemctl --user start socksproxyman.service")

@app.command()
def list() -> None:
    """List all proxies"""
    
    typer.secho("\nProxies list:\n", fg=typer.colors.BLUE, bold=True)
    columns = (
        "ID.  ",
        "| Host  ",
        "| Target  ",
    )
    headers = "".join(columns)
    typer.secho(headers, fg=typer.colors.BLUE, bold=True)
    typer.secho("-" * len(headers), fg=typer.colors.BLUE)
    for i in settings.tunnels:
        
        typer.secho(
            f"{i['name']}{(len(columns[0]) - len(str(i['name']))) * ' '}"
            f"| ({i['host']}){(len(columns[1]) - len(str(i['host'])) - 4) * ' '}"
            f"| {i['target']}{(len(columns[2]) - len(str(i['target'])) - 2) * ' '}",
            fg=typer.colors.BLUE,
        )
    typer.secho("-" * len(headers) + "\n", fg=typer.colors.BLUE)

@app.command()
def add(
    name2: str = typer.Argument("None"),
    host2: str = typer.Argument("None"),
    target2: str = typer.Argument("None"),
    name: str = typer.Option("None", "--name", "-n"),
    host: str = typer.Option("None", "--host", "-h"),
    target: str = typer.Option("None", "--target", "-t"),
    edit: bool = typer.Option(False, "--edit", "-e")
) -> None:
   """Add or Edit Proxies"""
   if edit:
       if name == "None":
         typer.secho(
           'No tunnel name provided for editing', fg=typer.colors.RED
         )
         raise typer.Exit(1)
       if ((name2 == "None") or (host2 == "None") or (target2 == "None")):
          typer.secho(
           'Put noedit in place of data you want to keep', fg=typer.colors.RED
         )
       
          raise typer.Exit(1)
       for i in settings.tunnels:
         if i["name"] == name :
           if name2 != "noedit":
              i["editname"] = name2
           if host2 != "noedit":
              i["host"] = host2
           if target2 != "noedit":
              i["target"] = target2
           settings.save()
           typer.secho(
           'Proxy edited', fg=typer.colors.GREEN
           )
           return
       typer.secho(
       'Proxy not found', fg=typer.colors.RED
       )
       raise typer.Exit(1)
   else:
      if name2 != "None":
         name = name2
         host = host2
         target = target2
      if name == "None":
           typer.secho(
           'No args provided', fg=typer.colors.RED
           )
           raise typer.Exit(1)
      for i in settings.tunnels:
         if i["name"] == name:
           typer.secho(
           'Proxy already exists', fg=typer.colors.RED
           )
           raise typer.Exit(1)
      settings.add_tunnels(name, host, target)
      typer.secho(
       'Proxy added', fg=typer.colors.GREEN
       )


@app.command()
def delete(
        name2: str = typer.Argument("None"),
        name: str = typer.Option("None", "--name")
) -> None:
   """Delete Proxies"""
   if name2 != "None":
      name = name2
   elif name == "None":
     typer.secho(
            'No args provided', fg=typer.colors.RED
        )
     raise typer.Exit(1)
   result = settings.delete_tunnels(name)
   if result == "ok":
      typer.secho(
            'Proxy deleted', fg=typer.colors.GREEN
        )
   else:
      typer.secho(
            'Proxy not found', fg=typer.colors.RED
        )
      raise typer.Exit(1)



@app.command()
def daemon() -> None:
   """Only used in a service"""
   import time
   import signal

   file = 0

   pidfiles = []

   for i in settings.tunnels:
     logger.info("Staring tunnel for " + i["name"] + " from " + i['host'] + " to " + i['target'])
     os.system('nohup /usr/local/bin/go run proxy.go -local "' + i['host'] + '" -target "' + i['target'] + '"  &')
#     os.system('echo $! > /tmp/socksman/' + str(file) + '.txt')
 #    pidfiles.append('/tmp/socksman/' + str(file) + '.txt')
  #   file = file + 1

   class GracefulKiller:
    kill_now = False
    def __init__(self):
      signal.signal(signal.SIGINT, self.exit_gracefully)
      signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
       self.kill_now = True
   
   killer = GracefulKiller()
   while not killer.kill_now:
     time.sleep(0.05)

   logger.info("Killing go proxies")
   os.system('./kill.sh')
   logger.info("Shutting down")
