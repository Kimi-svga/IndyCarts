import os

# Папки, которые нужно полностью игнорировать (чтобы не считать миллионы строк в зависимостях)
IGNORE_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', 'out', 
    'venv', '.venv', 'env', '__pycache__', '.github'
}

# Маппинг расширений к понятным названиям языков
LANGUAGE_MAP = {
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript (React)',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript (React)',
    '.json': 'JSON Configuration',
    '.css': 'CSS Styles',
    '.scss': 'SCSS Styles',
    '.html': 'HTML',
    '.py': 'Python',
    '.md': 'Markdown Documentation',
    '.yml': 'YAML (CI/CD)'
}

def is_comment_or_empty(line, ext):
    """Проверяет, является ли строка пустой или комментарием"""
    line = line.strip()
    if not line:
        return True
    
    # Базовая проверка для JS/TS/CSS
    if ext in ['.ts', '.tsx', '.js', '.jsx', '.css', '.scss']:
        if line.startswith('//') or line.startswith('/*') or line.startswith('*'):
            return True
            
    # Базовая проверка для Python/YAML
    elif ext in ['.py', '.yml']:
        if line.startswith('#'):
            return True
            
    return False

def analyze_project():
    stats = {}
    
    # Сканируем дерево каталогов
    for root, dirs, files in os.walk('.'):
        # Исключаем ненужные папки на лету
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in LANGUAGE_MAP:
                lang = LANGUAGE_MAP[ext]
                file_path = os.path.join(root, file)
                
                # Пропускаем сам скрипт анализа, если он лежит в корне
                if file == 'code_stats.py':
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    # Считаем только значащие строки кода
                    code_lines_count = sum(1 for line in lines if not is_comment_or_empty(line, ext))
                    
                    if lang not in stats:
                        stats[lang] = {'files': 0, 'lines': 0}
                        
                    stats[lang]['files'] += 1
                    stats[lang]['lines'] += code_lines_count
                except Exception:
                    # Игнорируем файлы, которые не удалось прочитать (например, бинарники)
                    pass

    # Вывод результатов в консоль
    print("\n" + "="*50)
    print(f"{'ЯЗЫК ПРОГРАММИРОВАНИЯ':<25} | {'ФАЙЛЫ':<6} | {'ЧИСТЫЕ СТРОКИ':<12}")
    print("="*50)
    
    total_files = 0
    total_lines = 0
    
    # Сортируем по количеству строк (от большего к меньшему)
    for lang, data in sorted(stats.items(), key=lambda x: x[1]['lines'], reverse=True):
        print(f"{lang:<25} | {data['files']:<6} | {data['lines']:<12,}")
        total_files += data['files']
        total_lines += data['lines']
        
    print("="*50)
    print(f"{'ИТОГО ПО ПРОЕКТУ':<25} | {total_files:<6} | {total_lines:<12,}")
    print("="*50 + "\n")

if __name__ == "__main__":
    analyze_project()
