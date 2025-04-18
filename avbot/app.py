import typer
import time
from typing import Optional
from pathlib import Path

from avbot.lib.screen import WoWclient
from avbot.lib.movements import moves
from avbot.lib.battlegrounds import afk_bg
from avbot.lib.fused_wiring import farm_fused_wiring

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

    # Initialize the WoW client
    typer.echo(f"Initializing WoW client...")
    wow_client = WoWclient()

    # Find and update client screen
    typer.echo(f"Detecting WoW window...")
    wow_client.find_screen()
    wow_client.update_client_image()

    # Load images and keystrokes
    typer.echo(f"Loading recognition images and keystroke patterns...")
    wow_client.load_sub_images()
    wow_client.load_movements()

    # Start the bot
    typer.echo(f"Starting AFK bot for {games} battlegrounds...")
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


@app.command("farm-fused-wiring")
def farm_wiring(
    dummies: int = typer.Option(
        25,
        "--dummies",
        "-d",
        help="Number of dummies to be used",
    ),
    dummy_key: str = typer.Option(
        "3",
        "--key",
        "-k",
        help="The target dummy keybind",
    ),
):
    """
    Uses then loots target dummies in order to farm fused wiring.
    """
    wow_client = WoWclient()
    wow_client.find_screen()
    wow_client.load_sub_images()
    wow_client.focus_client()

    farm_fused_wiring(wow_client, target_dummy_key=dummy_key, n=dummies)
    typer.echo(f"✅ Used and looted {dummies} target dummies.")


@app.command("save-screen")
def save_screen(
    folder_path: str = typer.Option(
        "./tests/data",
        "--folder",
        "-f",
        help="File save path",
    ),
    file_name: Optional[str] = typer.Option(
        "",
        "--name",
        "-n",
        help="File name",
    ),
):
    """
    Saves a WoW screenshot using the currently open WoW client.
    """
    # Use current timestamp if no filename is provided
    file_name = file_name if file_name else f"{int(time.time())}"
    file_name = file_name.split(".")[0]
    file_path = Path(folder_path) / f"{file_name}.png"

    # Initialize the WoW client
    typer.echo(f"Initializing WoW client...")
    wow_client = WoWclient()

    # Find and update client screen
    typer.echo(f"Detecting WoW window...")
    wow_client.find_screen()
    wow_client.update_client_image()

    # Save image
    typer.echo(f"Saving screenshot...")
    wow_client.image.save(file_path)
    typer.echo(f"✅ File saved at: {file_path}")


@app.command("move")
def move_character(
    units: float = typer.Option(
        10.0,
        "--units",
        "-u",
        help="Number of units moved",
    ),
    rotation: float = typer.Option(
        0.0,
        "--rotation",
        "-r",
        help="Rotation factor",
    ),
    move_forward_key: str = typer.Option(
        "w",
        "--forward",
        "-w",
        help="Key to move forward",
    ),
    turn_left_key: str = typer.Option(
        "[",
        "--left",
        "-a",
        help="Key to turn left",
    ),
    turn_right_key: str = typer.Option(
        "]",
        "--right",
        "-d",
        help="Key to turn right",
    ),
    mounted: int = typer.Option(
        0,
        "--mounted",
        "-m",
        help="If we are mounted",
    ),
):
    """
    Moves your character.
    """
    # Initialize the WoW client
    typer.echo(f"Initializing WoW client...")
    wow_client = WoWclient()

    # Find and update client screen
    typer.echo(f"Detecting WoW window...")
    wow_client.find_screen()
    wow_client.focus_client()

    # Move
    moves(
        movements=[{"units": units, "rotation": rotation}],
        move_forward_key=move_forward_key,
        turn_left_key=turn_left_key,
        turn_right_key=turn_right_key,
        stop_event=None,
        mounted=bool(mounted),
    )

    typer.echo(f"✅ Moved {units} units with a {round(rotation * 360)} degree rotation")


if __name__ == "__main__":
    app()
