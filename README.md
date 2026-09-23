# Gem-Gem

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![pygame-ce](https://img.shields.io/badge/Library-pygame--ce-1D9BF0?logo=pygame&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

</div>

**Gem-Gem** is a colorful and highly addictive Match-3 puzzle game developed entirely in Python. Designed with a focus on smooth gameplay and satisfying interactions, the game features dynamic gem swapping, intuitive matching algorithms, and immersive sound effects. 

Whether you are looking to kill some time or study the source code for building your own Python games, Gem-Gem provides a clean, well-structured example of 2D game mechanics.

## 🎮 Features

- **Classic Match-3 Mechanics**: Swap adjacent gems to form vertical or horizontal lines of three or more matching gems.
- **Dynamic Feedback**: Satisfying audio cues for successful matches (`match0.wav` to `match5.wav`) and error sounds for invalid swaps (`badswap.wav`).
- **Rich Visuals**: Seven distinct, colorful gem sprites (`gem1.png` to `gem7.png`) that pop on the screen.
- **Standalone Executable Support**: Comes with a PyInstaller specification file (`Gem-Gem.spec`) to easily compile the game into a standalone executable.
- **Automated Builds**: Integrated GitHub Actions workflow (`build.yml`) for automated testing and packaging.

## 🧪 Local Setup & Installation

To run the game locally on your machine, follow these steps:

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Gem-Gem.git
   cd Gem-Gem
   ```

2. **Create a virtual environment** (Recommended)
   ```bash
   python -m venv venv
   ```
   *On Windows:*
   ```powershell
   .\venv\Scripts\activate
   ```
   *On Linux/macOS:*
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install pygame-ce
   ```

## 🚀 Running the Game

To start playing, simply execute the main Python file:
```bash
python Gem-Gem.py
```

### Building the Executable
If you wish to create a standalone executable that doesn't require Python to be installed, use PyInstaller with the provided spec file:
```bash
pip install pyinstaller
pyinstaller Gem-Gem.spec
```
The executable will be located in the `dist/` folder.

## 🏗️ Project Structure

```text
Gem-Gem/
├── .github/workflows/       # CI/CD pipelines (build.yml)
├── screenshots/             # Gameplay images
├── *.png                    # Gem sprites (gem1.png - gem7.png)
├── *.wav                    # Audio assets (match sounds, badswap)
├── Gem-Gem.py               # Main game logic and entry point
├── Gem-Gem.spec             # PyInstaller configuration
└── .gitignore               # Git ignore file
```

## 📜 License

This project is open-source and available under the MIT License. Feel free to fork, modify, and distribute it!
