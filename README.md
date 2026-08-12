# gargomem-bot

Gargomem-bot is a sophisticated, asynchronous automation tool designed for a 2D browser-based MMORPG. It leverages browser automation to perform various in-game tasks, from experience grinding to complex, multi-map heroes hunting. The bot features an injectable in-game UI for control, advanced pathfinding algorithms, and robust Discord integration for notifications and remote decision-making.

## Features

*   **Multi-Mode Automation**:
    *   **EXP Service**: Automatically grinds on selected monster groups based on the character's level.
    *   **E2 Service**: Farms Elite II monsters by calculating respawn times and managing logout/login cycles to optimize efficiency.
    *   **Heroes Service**: An advanced module for hunting rare, powerful heroes across the entire game world.
*   **Advanced Navigation and Pathfinding**:
    *   Utilizes A* for efficient pathfinding on individual maps.
    *   Navigates between maps using a world graph and Breadth-First Search (BFS).
    *   The heroes hunting module employs route optimization (approximating the Traveling Salesman Problem with Held-Karp) to plan the most efficient scanning paths.
*   **Discord Integration**:
    *   Sends real-time notifications about valuable loot to a specified Discord webhook.
    *   When a heroes is found, it uses a Discord bot to request user input (Attack, Wait, or Logout) via reactions, enabling remote control over critical decisions.
*   **Intelligent Systems**:
    *   **Captcha Solver**: Automatically resolves in-game captchas by identifying and clicking buttons marked with a star.
    *   **Movement Guard**: Detects when the character is stuck or immobilized and performs corrective movements.
    *   **Auto-Healing**: Monitors character health and uses potions as needed.
*   **Custom In-Game UI**:
    *   Injects a custom control panel directly into the game's web page.
    *   Allows the user to easily select the desired automation mode (EXP, E2, or Heroes hunting).
*   **Tutorial Automation**: Includes scripts to automatically complete the game's initial tutorial quests.

## Architecture

*   **`main.py`**: The application's entry point. It initializes the browser driver, handles game authentication, and starts the core bot loop and background tasks (healing, captcha checks).
*   **Services (`bot/game/services/`)**:
    *   `exp_service.py`: Logic for continuous monster farming.
    *   `e2_service.py`: State machine for farming Elite II monsters, including respawn timers.
    *   `heroes_service.py`: A highly complex module for finding heroes. It computes optimal scanning routes, manages a list of remaining maps, and orchestrates travel and detection across the game world.
*   **Navigation (`bot/game/navigation/` & `bot/game/moving/`)**:
    *   Contains the A* pathfinding implementation (`pathfinding.py`) for on-map movement.
    *   Manages the world map graph (`world_graph.py`) and inter-map travel logic.
*   **Core (`bot/core/`)**:
    *   `driver.py`: Manages the browser automation instance (created from `driver.template.py`).
    *   `captcha.py`: Detects and solves captchas.
    *   `movement_guard.py`: Handles character immobilization events.
*   **Integrations (`bot/integrations/`)**:
    *   `dsc_loot_notifier.py`: Sends messages to Discord webhooks.
    *   `dsc_reaction_control.py`: Manages the Discord bot for interactive decision-making.
*   **UI (`bot/ui/`)**:
    *   `botUI.py`: Contains the JavaScript code to inject and manage the in-game control panel.

## Setup

1.  **Clone the Repository**:
    ```sh
    git clone https://github.com/Nejtos/gargomem-bot.git
    cd gargomem-bot
    ```

2.  **Install Dependencies**:
    Install the required Python packages. It is recommended to use a virtual environment. Key dependencies include `asyncio`, `playwright`, `python-dotenv`, and `discord.py`.

3.  **Configure Driver**:
    The repository includes a template for the browser driver.
    *   Rename `bot/core/driver.template.py` to `bot/core/driver.py`.
    *   Edit `driver.py` to implement the `init_driver` method with your browser automation setup (e.g., Playwright with a specific browser profile).

4.  **Configure Game Data**:
    The bot relies on game world data.
    *   Rename `bot/data/world_maps.template.json` to `bot/data/world_maps.json`.
    *   Populate `world_maps.json` with the complete map and gateway data from the game.

5.  **Create Environment File**:
    Create a `.env` file in the root directory and add the following variables:
    ```env
    # URL of the game's login page
    GAME_URL="https://game.url.com"

    # Discord Bot Token for reaction-based controls
    DISCORD_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN"

    # Discord Webhook for general loot notifications
    DISCORD_WEBHOOK_URL="YOUR_LOOT_WEBHOOK_URL"

    # Discord Webhook for heroes-specific loot and detection notifications
    DISCORD_WEBHOOK_HEROES_URL="YOUR_HERO_WEBHOOK_URL"
    ```

## Usage

1.  **Start the Bot**:
    Run the `main.py` script from your terminal, providing a profile number as a command-line argument. This number corresponds to the browser profile you configured in `driver.py`.
    ```sh
    python main.py <profile_number>
    ```
    Example:
    ```sh
    python main.py 1
    ```

2.  **Control the Bot**:
    *   Once the bot logs into the game, a "N8Bot" icon will appear on the screen. Click it to open the control panel.
    *   Use the dropdown menus to select the desired activity (EXP grinding, E2 farming, or heroes hunting) and click "Select".
    *   The bot will begin its task.

3.  **Stop the Bot**:
    To safely stop the bot and close the browser, press the `|` (pipe) key in the terminal window where the bot is running.
