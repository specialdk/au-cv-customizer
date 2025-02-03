import subprocess
import sys
import os

def install_dependencies():
    # Upgrade pip
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    
    # Install requirements
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # Download SpaCy language model
    subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_lg'])
    
    print("✅ Pro Tier Dependencies Installed Successfully!")
    print("Next steps:")
    print("1. Set your OpenAI API key in .env")
    print("2. Configure Stripe Pro subscription")

if __name__ == '__main__':
    install_dependencies()
