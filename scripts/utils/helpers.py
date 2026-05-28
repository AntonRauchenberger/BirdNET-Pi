import glob
import json
import os
import re
import subprocess
from collections import OrderedDict
from configparser import ConfigParser
from itertools import chain
from .benchmarking import BenchmarkService

_settings = None

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(BASE_PATH, 'scripts/birds.db')
MODEL_PATH = os.path.join(BASE_PATH, 'model')
FONT_DIR = os.path.join(BASE_PATH, 'homepage/static')
ANALYZING_NOW = os.path.expanduser('~/BirdSongs/StreamData/analyzing_now.txt')

class BenchmarkingServiceProxy:
    def __init__(self):
        self._service: BenchmarkService | None = None

    def set(self, service: BenchmarkService | None) -> None:
        self._service = service

    def __bool__(self):
        return self._service is not None

    def __getattr__(self, name):
        if self._service is None:
            raise RuntimeError("Benchmarking service has not been initialized")
        return getattr(self._service, name)

BENCHMARKING_SERVICE: BenchmarkingServiceProxy = BenchmarkingServiceProxy()

BENCHMARKING_RESULTS_DIR = os.path.join(BASE_PATH, 'benchmarking_results')


def get_font():
    conf = get_settings()
    if conf['DATABASE_LANG'] == 'ar':
        ret = {'font.family': 'Noto Sans Arabic', 'path': os.path.join(FONT_DIR, 'NotoSansArabic-Regular.ttf')}
    elif conf['DATABASE_LANG'] in ['ja', 'zh_CN', 'zh_TW']:
        ret = {'font.family': 'Noto Sans JP', 'path': os.path.join(FONT_DIR, 'NotoSansJP-Regular.ttf')}
    elif conf['DATABASE_LANG'] == 'ko':
        ret = {'font.family': 'Noto Sans KR', 'path': os.path.join(FONT_DIR, 'NotoSansKR-Regular.ttf')}
    elif conf['DATABASE_LANG'] == 'th':
        ret = {'font.family': 'Noto Sans Thai', 'path': os.path.join(FONT_DIR, 'NotoSansThai-Regular.ttf')}
    else:
        ret = {'font.family': 'Roboto Flex', 'path': os.path.join(FONT_DIR, 'RobotoFlex-Regular.ttf')}
    return ret


class PHPConfigParser(ConfigParser):
    def get(self, section, option, *, raw=False, vars=None, fallback=None):
        value = super().get(section, option, raw=raw, vars=vars, fallback=fallback)
        if raw:
            return value
        else:
            return value.strip('"')


def _load_settings(settings_path='/etc/birdnet/birdnet.conf', force_reload=False):
    global _settings
    if _settings is None or force_reload:
        with open(settings_path) as f:
            parser = PHPConfigParser(interpolation=None)
            # preserve case
            parser.optionxform = lambda option: option
            lines = chain(("[top]",), f)
            parser.read_file(lines)
            _settings = parser['top']
    return _settings


def get_settings(settings_path='/etc/birdnet/birdnet.conf', force_reload=False):
    settings = _load_settings(settings_path, force_reload)
    return settings

def save_settings(settings_path='/etc/birdnet/birdnet.conf', new_settings: dict = None):
    if not new_settings:
        return
    if not isinstance(new_settings, dict):
        raise TypeError('new_settings must be a dict')

    def _format_value(value, quote: bool | None = None) -> str:
        if isinstance(value, bool):
            value_str = '1' if value else '0'
        elif value is None:
            value_str = ''
        else:
            value_str = str(value)

        if quote is None:
            quote = (value_str == '' or any(ch.isspace() for ch in value_str))

        if quote:
            escaped = value_str.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        return value_str

    updates = {str(key): value for key, value in new_settings.items()}
    line_pattern = re.compile(r'^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$')

    # Read existing settings and apply updates
    with open(settings_path, 'r') as conf_file:
        lines = conf_file.readlines()

    updated_lines = []
    for line in lines:
        if line.lstrip().startswith('#'):
            updated_lines.append(line)
            continue

        match = line_pattern.match(line.rstrip('\n'))
        if not match:
            updated_lines.append(line)
            continue

        key = match.group(2)
        if key not in updates:
            updated_lines.append(line)
            continue

        existing_raw_value = match.group(3).strip()
        use_quotes = existing_raw_value.startswith('"') and existing_raw_value.endswith('"')
        formatted_value = _format_value(updates.pop(key), quote=use_quotes)
        updated_lines.append(f'{match.group(1)}{key}={formatted_value}\n')

    if updates:
        if updated_lines and updated_lines[-1] and not updated_lines[-1].endswith('\n'):
            updated_lines[-1] = f"{updated_lines[-1]}\n"
        if updated_lines and updated_lines[-1].strip() != '':
            updated_lines.append('\n')
        for key, value in updates.items():
            updated_lines.append(f'{key}={_format_value(value)}\n')

    contents = ''.join(updated_lines)
    temp_path = f'{settings_path}.tmp'

    # Attempt to write, fallback to sudo if permission is denied
    try:
        with open(temp_path, 'w') as conf_file:
            conf_file.write(contents)
        os.replace(temp_path, settings_path)
    except PermissionError:
        try:
            sudo_result = subprocess.run(
                ['sudo', '-n', 'tee', settings_path],
                input=contents,
                text=True,
                capture_output=True,
                check=False,
            )
            if sudo_result.returncode != 0:
                stderr = sudo_result.stderr.strip()
                raise PermissionError(
                    f'Unable to write settings file {settings_path}: {stderr or "sudo write failed"}'
                )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # Invalidate cache so subsequent reads observe persisted updates
    global _settings
    _settings = None
    _load_settings(settings_path=settings_path, force_reload=True)

def save_single_setting(key, value, settings_path='/etc/birdnet/birdnet.conf'):
    save_settings(settings_path=settings_path, new_settings={key: value})


def get_open_files_in_dir(dir_name):
    result = subprocess.run(['lsof', '-w', '-Fn', '+D', f'{dir_name}'], check=False, capture_output=True)
    ret = result.stdout.decode('utf-8')
    err = result.stderr.decode('utf-8')
    if err:
        raise RuntimeError(f'{ret}:\n {err}')
    names = [line.lstrip('n') for line in ret.splitlines() if line.startswith('n')]
    return names


def get_wav_files():
    conf = get_settings()
    files = (glob.glob(os.path.join(conf['RECS_DIR'], '*/*/*.wav')) +
             glob.glob(os.path.join(conf['RECS_DIR'], 'StreamData/*.wav')))
    files.sort()
    files = [os.path.join(conf['RECS_DIR'], file) for file in files]
    rec_dir = os.path.join(conf['RECS_DIR'], 'StreamData')
    open_recs = get_open_files_in_dir(rec_dir)
    files = [file for file in files if file not in open_recs]
    return files


def get_language(language=None):
    if language is None:
        language = get_settings()['DATABASE_LANG']
    file_name = os.path.join(MODEL_PATH, f'l18n/labels_{language}.json')
    with open(file_name) as f:
        ret = json.loads(f.read())
    return ret


def save_language(labels, language):
    file_name = os.path.join(MODEL_PATH, f'l18n/labels_{language}.json')
    with open(file_name, 'w') as f:
        f.write(json.dumps(OrderedDict(sorted(labels.items())), indent=2, ensure_ascii=False))


def get_model_labels(model=None):
    if model is None:
        model = get_settings()['MODEL']
    file_name = os.path.join(MODEL_PATH, f'{model}_Labels.txt')
    with open(file_name) as f:
        labels = [line.strip() for line in f.readlines()]
    if labels and labels[0].count('_') == 1:
        labels = [re.sub(r'_.+$', '', label) for label in labels]
    return labels


def set_label_file():
    lang = get_language()
    labels = [f'{label}_{lang[label]}\n' for label in get_model_labels()]
    file_name = os.path.join(MODEL_PATH, 'labels.txt')
    if os.path.islink(file_name):
        os.remove(file_name)
    with open(file_name, 'w') as f:
        f.writelines(labels)
