#!/usr/bin/env python3
"""
Setup script for the Trading Bot
Installs dependencies and configures the environment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")


def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    # Upgrade pip first
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                   check=False, capture_output=True)
    
    # Install requirements
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print("❌ Failed to install dependencies")
            print(result.stderr)
            sys.exit(1)
    else:
        print("❌ requirements.txt not found")
        sys.exit(1)


def setup_environment():
    """Setup environment configuration"""
    print("\n⚙️  Setting up environment...")
    
    env_example = Path(__file__).parent / ".env.example"
    env_file = Path(__file__).parent / ".env"
    
    if env_file.exists():
        print("⚠️  .env file already exists")
        response = input("   Do you want to overwrite it? (y/n): ")
        if response.lower() != 'y':
            print("   Keeping existing .env file")
            return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("\n⚠️  IMPORTANT: Edit the .env file and add your Backpack API credentials")
        print("   1. Open .env file")
        print("   2. Replace 'your_api_key_here' with your actual API key")
        print("   3. Replace 'your_api_secret_here' with your actual API secret")
    else:
        print("❌ .env.example not found")
        sys.exit(1)


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    dirs_to_create = ['logs', 'data']
    base_path = Path(__file__).parent
    
    for dir_name in dirs_to_create:
        dir_path = base_path / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"   ✅ {dir_name}/")


def test_imports():
    """Test if all required modules can be imported"""
    print("\n🧪 Testing imports...")
    
    required_modules = [
        'requests',
        'websocket',
        'numpy',
        'pandas',
        'dotenv',
        'colorlog'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("   Try running: pip install " + " ".join(failed_imports))
        sys.exit(1)


def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "=" * 50)
    print("✅ SETUP COMPLETE!")
    print("=" * 50)
    
    print("\n📋 NEXT STEPS:")
    print("-" * 30)
    print("1. Edit the .env file with your Backpack API credentials")
    print("   $ nano .env  (or use your preferred editor)")
    print("\n2. Test the connection:")
    print("   $ python src/test_connection.py")
    print("\n3. Start the trading bot:")
    print("   $ python src/trading_bot.py")
    print("\n4. Monitor the bot (in a separate terminal):")
    print("   $ python src/monitor.py")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("-" * 30)
    print("• Start with TESTNET first (set USE_TESTNET=true in .env)")
    print("• Test thoroughly before using real funds")
    print("• Monitor closely during initial runs")
    print("• Set appropriate stop-loss levels")
    print("• Never invest more than you can afford to lose")
    
    print("\n📚 For more information, see README.md")
    print("=" * 50)


def main():
    """Main setup function"""
    print("=" * 50)
    print("TRADING BOT SETUP")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Setup environment
    setup_environment()
    
    # Create directories
    create_directories()
    
    # Test imports
    test_imports()
    
    # Display next steps
    display_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)