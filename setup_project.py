from pathlib import Path

def create_project_structure():
    """Proje yapısını oluştur"""
    directories = [
        'config',
        'handlers',
        'services',
        'utils',
        'web',
        'data/user_data',
        'data/chat_history',
        'data/user_credits'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        Path(directory) / '__init__.py'

if __name__ == '__main__':
    create_project_structure() 