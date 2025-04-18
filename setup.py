from setuptools import setup, find_packages

setup(
    name="avbot",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyautogui",
        "numpy",
        "pygetwindow",
        "pillow",
        "psutil",
        "screeninfo",
        "mss",
        "opencv-python",
        "keyboard",
        "typer[all]",
        "pynput",
    ],
    entry_points={
        "console_scripts": [
            "avbot=avbot.app:app",
        ],
    },
    package_data={
        "avbot": ["data/*", "keystrokes/*"],
    },
    description="Bot for automating AFK battlegrounds in World of Warcraft",
    python_requires=">=3.7",
)
