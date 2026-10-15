import os
import sys

IGNORE_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', 'out', 
    'venv', '.venv', 'env', '__pycache__', '.github'
}

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
    line = line.strip()
    if not line:
        return True
    if ext in ['.ts', '.tsx', '.js', '.jsx', '.css', '.scss']:
        if line.startswith('//') or line.startswith('/*') or line.startswith('*'):
            return True
    elif ext in ['.py', '.yml']:
        if line.startswith('#'):
            return True
    return False

def analyze_project():
    stats = {}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            ext = os.path.splitext(file).lower()
            if ext in LANGUAGE_MAP and file != 'code_stats.py':
                lang = LANGUAGE_MAP[ext]
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    code_lines_count = sum(1 for line in lines if not is_comment_or_empty(line, ext))
                    if lang not in stats:
                        stats[lang] = {'files': 0, 'lines': 0}
                    stats[lang]['files'] += 1
                    stats[lang]['lines'] += code_lines_count
                except Exception:
                    pass

    # Форматированный вывод в логи Render
    print("\n" + "[CODE METRICS] " + "="*45)
    print(f"[CODE METRICS] {'ЯЗЫК ПРОГРАММИРОВАНИЯ':<22} | {'ФАЙЛЫ':<5} | {'ЧИСТЫЕ СТРОКИ':<12}")
    print("[CODE METRICS] " + "="*45)
    
    total_files, total_lines = 0, 0
    for lang, data in sorted(stats.items(), key=lambda x: x['lines'], reverse=True):
        print(f"[CODE METRICS] {lang:<22} | {data['files']:<5} | {data['lines']:<12,}")
        total_files += data['files']
        total_lines += data['lines']
        
    print("[CODE METRICS] " + "="*45)
    print(f"[CODE METRICS] {'ИТОГО ПО ПРОЕКТУ':<22} | {total_files:<5} | {total_lines:<12,}")
    print("[CODE METRICS] " + "="*45 + "\n")
    sys.stdout.flush()

if __name__ == "__main__":
    analyze_project()
