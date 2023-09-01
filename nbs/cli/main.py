import logging

import typer

from cli.commands import preprocess, segment, clutch, ingest, worker

app = typer.Typer()
logger = logging.getLogger(__name__)

# Subcommands
app.add_typer(preprocess.app, name='prep')
app.add_typer(segment.app, name='segment')
app.add_typer(clutch.app, name='clutch')
app.add_typer(ingest.app, name='ingest')
app.add_typer(worker.app, name='worker')

@app.callback()
def main_callback(ctx: typer.Context, log_level: str = typer.Option("INFO", "--log-level")):
    logging.basicConfig(format='[%(levelname)8s] %(asctime)s %(filename)16s:L%(lineno)-3d %(funcName)16s() : %(message)s', level=log_level)
    pass

if __name__ == '__main__':
    app()
