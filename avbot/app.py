import typer
from typing import Optional

# Create the app correctly - this is what the CLI will use
app = typer.Typer(help="Automated World of Warcraft battleground bot")


@app.command("afk-av")
def afk_av(
    games: int = typer.Option(
        25,
        "--games",
        "-g",
        help="Number of battleground games to complete",
    ),
    target_name: str = typer.Option(
        "Thelman Slatefist",
        "--target",
        "-t",
        help="Name of the NPC to target for queuing",
    ),
    interact_key: str = typer.Option(
        "/",
        "--interact",
        "-i",
        help="Key to press for interacting with the target",
    ),
    mount_key: str = typer.Option(
        "t",
        "--mount",
        "-m",
        help="Keybind to mount up",
    ),
    threshold: float = typer.Option(
        0.75,
        "--threshold",
        help="Image recognition matching threshold (0.0-1.0)",
    ),
    max_wait_time: int = typer.Option(
        400,
        "--wait-time",
        "-w",
        help="Maximum wait time in seconds for battleground queue",
    ),
):
    """
    Run the Alterac Valley AFK farming bot.

    This bot will automatically queue for Alterac Valley battlegrounds,
    enter when the queue pops, and perform necessary movements to avoid
    AFK detection while farming honor/marks.
    """
    from avbot.lib.screen import WoWclient
    from avbot.lib.battlegrounds import afk_bg

    # Initialize the WoW client
    typer.echo(f"🎮 Initializing WoW client...")
    wow_client = WoWclient()

    # Find and update client screen
    typer.echo(f"🔍 Detecting WoW window...")
    wow_client.find_screen()
    wow_client.update_client_image()

    # Load images and keystrokes
    typer.echo(f"📂 Loading recognition images and keystroke patterns...")
    wow_client.load_sub_images()
    wow_client.load_keystrokes()

    # Start the bot
    typer.echo(f"🚀 Starting AFK bot for {games} battlegrounds...")
    try:
        afk_bg(
            wow_client,
            n=games,
            target_name=target_name,
            interact_with_target_key=interact_key,
            mount_key=mount_key,
            threshold=threshold,
            max_wait_time=max_wait_time,
        )
        typer.echo(f"✅ Bot routine completed successfully!")
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
