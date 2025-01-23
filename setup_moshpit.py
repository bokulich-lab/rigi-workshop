"""Set up QIIME 2 on Google Colab.

Do not use this on a local machine, especially not as an admin!
"""

import os
import sys
from subprocess import Popen, PIPE

r = Popen(["pip", "install", "rich"])
r.wait()
from rich.console import Console  # noqa
con = Console()

has_conda = "conda version" in os.popen("conda info").read()
has_qiime = "QIIME 2 release:" in os.popen("qiime info").read()


MINICONDA_INSTALLER = "Miniconda3-py310_24.11.1-0-Linux-x86_64.sh"
MINICONDA_PATH = (
    f"https://repo.anaconda.com/miniconda/{MINICONDA_INSTALLER}"
)


def cleanup():
    """Remove downloaded files."""
    if os.path.exists(MINICONDA_INSTALLER):
        os.remove(MINICONDA_INSTALLER)
    con.log("Cleaned up unneeded files.")


def run_and_check(
        args, check, message, failure, success, console=con, env_vars=None,
        check_returncode=True
):
    """Run a command and check that it worked."""
    console.log(message)
    env_vars = {**os.environ, **env_vars} if env_vars else os.environ
    r = Popen(args, env=env_vars, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    o, e = r.communicate()
    out = o + e

    if (check_returncode and r.returncode == 0 and check in out) or \
            (not check_returncode and check in out):
        console.log("[blue]%s[/blue]" % success)
    else:
        console.log("[red]%s[/red]" % failure, out)
        cleanup()
        sys.exit(1)


def _hack_in_the_plugins():
    """Add the plugins to QIIME."""
    import qiime2.sdk as sdk
    from importlib.metadata import entry_points

    pm = sdk.PluginManager(add_plugins=False)
    for entry in entry_points()["qiime2.plugins"]:
        plugin = entry.load()
        package = entry.value.split(':')[0].split('.')[0]
        pm.add_plugin(plugin, package, entry.name)


if __name__ == "__main__":
    if not has_conda:
        run_and_check(
            ["wget", MINICONDA_PATH],
            "saved",
            ":snake: Downloading miniconda...",
            "failed downloading miniconda :sob:",
            ":snake: Done."
        )

        run_and_check(
            ["bash", MINICONDA_INSTALLER, "-bfp", "/usr/local"],
            "installation finished.",
            ":snake: Installing miniconda...",
            "could not install miniconda :sob:",
            ":snake: Installed miniconda to `/usr/local` :snake:"
        )
    else:
        con.log(":snake: Miniconda is already installed. Skipped.")

    if not has_qiime:
        run_and_check(
            ["conda", "install", "mamba", "-y", "-n", "base",
             "-c", "conda-forge"],
            "mamba",
            ":mag: Installing mamba...",
            "could not install mamba :sob:",
            ":mag: Done."
        )

        run_and_check(
            ["wget", "https://raw.githubusercontent.com/qiime2/distributions/dev/latest/passed/qiime2-moshpit-ubuntu-latest-conda.yml"],
            "saved",
            ":evergreen_tree: Fetching the environment file...",
            "could not execute wget :sob:",
            ":evergreen_tree: Done."
        )

        run_and_check(
            ["mamba", "env", "create", "-n", "moshpit-dev", "-y",
             "--file", "qiime2-moshpit-ubuntu-latest-conda.yml"],
            "QIIME is caching",
            ":mag: Installing MOSHPIT. This may take a little bit.\n :clock1:",
            "could not install MOSHPIT :sob:",
            ":mag: Done."
        )

    else:
        con.log(":mag: MOSH is already installed. Skipped.")

    run_and_check(
        ["mamba", "run", "-n", "moshpit-dev", "-r", "/usr/local", "mosh" ,"info"],
        "QIIME 2 release:",
        ":bar_chart: Checking that MOSHPIT command line works...",
        "MOSHPIT command line does not seem to work :sob:",
        ":bar_chart: MOSHPIT command line looks good :tada:"
    )

    if sys.version_info[0:2] == (3, 8):
        sys.path.append("/usr/local/lib/python3.10/site-packages")
        con.log(":mag: Fixed import paths to include QIIME 2.")

        con.log(":bar_chart: Checking if QIIME 2 import works...")
        try:
            import qiime2  # noqa
        except Exception:
            con.log("[red]QIIME 2 can not be imported :sob:[/red]")
            sys.exit(1)
        con.log("[blue]:bar_chart: QIIME 2 can be imported :tada:[/blue]")

        con.log(":bar_chart: Setting up QIIME 2 plugins...")
        try:
            _hack_in_the_plugins()
            from qiime2.plugins import feature_table # noqa
        except Exception:
            con.log("[red]Could not add the plugins :sob:[/red]")
            sys.exit(1)
        con.log("[blue]:bar_chart: Plugins are working :tada:[/blue]")

    cleanup()

    con.log("[green]Everything is A-OK. "
            "You can start using MOSHPIT now :thumbs_up:[/green]")
