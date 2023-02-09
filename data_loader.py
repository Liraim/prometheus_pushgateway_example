import datetime
import random
import time
import logging

from prometheus_client import CollectorRegistry, push_to_gateway, Gauge

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

SEND_TIMEOUT = 10
registry = CollectorRegistry()
# create metrics
simple_gauge = Gauge('simple_gauge', 'Example Simple Gauge metric', registry=registry)
second_gauge = Gauge('second_gauge', 'Example Second Simple Gauge metric', registry=registry)

rand = random.Random()


def calculate_metrics():
    value = rand.random()
    simple_gauge.set(value)
    simple_gauge.set(value)


def main():
    last_send = datetime.datetime.now() - datetime.timedelta(seconds=10)
    for i in range(0, 100):
        calculate_metrics()
        # this sends all metrics to so prometheus can scrape it
        new_send = datetime.datetime.now()
        seconds_elapsed = (new_send - last_send).total_seconds()
        if seconds_elapsed < SEND_TIMEOUT:
            time.sleep(SEND_TIMEOUT - seconds_elapsed)
        push_to_gateway('localhost:9091', job='batchA', registry=registry)
        while last_send < new_send:
            last_send = last_send + datetime.timedelta(seconds=10)
        logging.info("data sent")


if __name__ == '__main__':
    main()
