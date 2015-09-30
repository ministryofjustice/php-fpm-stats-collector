#!/usr/bin/env python
import os
import sys
import socket
from time import sleep, time

import schedule
import requests
from statsd.defaults.env import statsd
import time

STATSD_DELAY = int(os.environ.get("STATSD_DELAY", 10))
FPM_STATUS_URL = os.environ.get("FPM_STATUS_URL","http://localhost/status")


METRICS_MAPPING = {
    "accepted conn": "accepted_conn",
    "listen queue": "listen_queue",
    "max listen queue": "max_listen_queue",
    "listen queue len": "listen_queue_len",
    "idle processes": "idle_processes",
    "active processes": "active_processes",
    "total processes": "total_processes",
    "max active processes": "max_active_processes",
    "max children reached": "max_children_reached",
    "slow requests": "slow_requests"
}


def get_fpm_stats(stats_url):
    """
    reads php-fpm/status page and parses it
    :param stats_url:
    :return: list of (metric, metric_value)
    """
    data = []
    try:
        r = requests.get(stats_url)
    except requests.exceptions.ConnectionError:
        print("Can't connect to {}".format(stats_url))
        return data
    if r.status_code == 200:
        raw_data = requests.get(stats_url).text
        for line in raw_data.splitlines():
            try:
                metric_name, metric_value = line.strip().split(":")
                if metric_name in METRICS_MAPPING.keys():
                    data.append((METRICS_MAPPING[metric_name],int(metric_value)))
            except ValueError:
                pass
    return data


def main():
    def report_stats():
        print("reporting")
        with statsd.pipeline() as pipe:
            for stat, value in get_fpm_stats(FPM_STATUS_URL):
                print(stat, value)
                pipe.gauge(stat, value)


    schedule.every(STATSD_DELAY).seconds.do(report_stats)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
