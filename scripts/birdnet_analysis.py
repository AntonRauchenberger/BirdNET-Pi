import logging
import os
import os.path
import re
import signal
import sys
import threading
from queue import Queue
from subprocess import CalledProcessError

import inotify.adapters
from inotify.constants import IN_CLOSE_WRITE

from utils.analysis import load_global_model, run_analysis
from utils.helpers import get_settings, get_wav_files, ANALYZING_NOW, BENCHMARKING_SERVICE
from utils.classes import ParseFileName
from utils.reporting import extract_detection, summary, write_to_file, write_to_db, apprise, bird_weather, heartbeat, \
    update_json_file
from utils.benchmarking import BenchmarkService

shutdown = False

log = logging.getLogger(__name__)


def sig_handler(sig_num, curr_stack_frame):
    global shutdown
    log.info('Caught shutdown signal %d', sig_num)
    shutdown = True


def main():
    load_global_model()
    conf = get_settings()
    i = inotify.adapters.Inotify()
    i.add_watch(os.path.join(conf['RECS_DIR'], 'StreamData'), mask=IN_CLOSE_WRITE)

    # Initialize benchmarking service
    # TODO test initialization
    conf = get_settings()
    model = conf['MODEL']
    project_path = conf['BASE_PATH']
    BENCHMARKING_SERVICE.set(
        BenchmarkService(model_path=os.path.join(conf["MODEL_PATH"], f'{model}.tflite'), project_path=project_path, enable_cpu_metrics=True,
                        scenario="Local Laptop")
    )

    backlog = get_wav_files()

    report_queue = Queue()
    thread = threading.Thread(target=handle_reporting_queue, args=(report_queue, ))
    thread.start()

    log.info('backlog is %d', len(backlog))
    for file_name in backlog:
        process_file(file_name, report_queue)
        if shutdown:
            break
    log.info('backlog done')

    empty_count = 0
    for event in i.event_gen():
        if shutdown:
            break

        if event is None:
            if empty_count > (conf.getint('RECORDING_LENGTH') * 2 + 30):
                log.error('no more notifications: restarting...')
                break
            empty_count += 1
            continue

        (_, type_names, path, file_name) = event
        if re.search('.wav$', file_name) is None:
            continue
        log.debug("PATH=[%s] FILENAME=[%s] EVENT_TYPES=%s", path, file_name, type_names)

        file_path = os.path.join(path, file_name)
        if file_path in backlog:
            # if we're very lucky, the first event could be for the file in the backlog that finished
            # while running get_wav_files()
            backlog = []
            continue

        process_file(file_path, report_queue)
        empty_count = 0

    # we're all done
    report_queue.put(None)
    thread.join()
    report_queue.join()


def process_file(file_name, report_queue):
    try:
        if os.path.getsize(file_name) == 0:
            os.remove(file_name)
            return
        log.info('Analyzing %s', file_name)
        with open(ANALYZING_NOW, 'w') as analyzing:
            analyzing.write(file_name)
        file = ParseFileName(file_name)

        BENCHMARKING_SERVICE.start_timer("total analysis")
        detections = run_analysis(file)

        # we join() to make sure te reporting queue does not get behind
        if not report_queue.empty():
            log.warning('reporting queue not yet empty')
        report_queue.join()
        report_queue.put((file, detections))
    except BaseException as e:
        stderr = e.stderr.decode('utf-8') if isinstance(e, CalledProcessError) else ""
        log.exception(f'Unexpected error: {stderr}', exc_info=e)
    finally:
        BENCHMARKING_SERVICE.stop_timer("total analysis")


def handle_reporting_queue(queue):
    while True:
        msg = queue.get()
        # check for signal that we are done
        if msg is None:
            break

        file, detections = msg
        try:
            BENCHMARKING_SERVICE.start_timer("total reporting")

            BENCHMARKING_SERVICE.start_timer("update json file")
            update_json_file(file, detections)
            BENCHMARKING_SERVICE.stop_timer("update json file")

            BENCHMARKING_SERVICE.start_timer("write to db and file")
            for detection in detections:
                detection.file_name_extr = extract_detection(file, detection)
                log.info('%s;%s', summary(file, detection), os.path.basename(detection.file_name_extr))
                write_to_file(file, detection)
                write_to_db(file, detection)
            BENCHMARKING_SERVICE.stop_timer("write to db and file")

            apprise(file, detections)

            BENCHMARKING_SERVICE.start_timer("soundscape POST to server")
            bird_weather(file, detections)
            BENCHMARKING_SERVICE.stop_timer("soundscape POST to server")

            heartbeat()
            os.remove(file.file_name)
        except BaseException as e:
            stderr = e.stderr.decode('utf-8') if isinstance(e, CalledProcessError) else ""
            log.exception(f'Unexpected error: {stderr}', exc_info=e)
        finally:
            BENCHMARKING_SERVICE.stop_timer("total reporting")

        queue.task_done()

    # TODO Add logging

    # mark the 'None' signal as processed
    queue.task_done()
    log.info('handle_reporting_queue done')


def setup_logging():
    logger = logging.getLogger()
    formatter = logging.Formatter("[%(name)s][%(levelname)s] %(message)s")
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    global log
    log = logging.getLogger('birdnet_analysis')


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    setup_logging()

    main()
