import datetime
import random
import time
import logging
import uuid

from prometheus_client import CollectorRegistry, push_to_gateway, Gauge
import psycopg

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


create_table_statement = """
drop table if exists metric_name;
create table metric_name(
    timestamp timestamp,
    value1 integer,
    value2 varchar,
    value3 float
)
"""


def prep_db():
    with psycopg.connect("host=localhost port=5432 user=postgres password=example", autocommit=True) as conn:
        res = conn.execute("SELECT 1 FROM pg_database WHERE datname='test'")
        if len(res.fetchall()) == 0:
            conn.execute("create database test;")
    with psycopg.connect("host=localhost port=5432 dbname=test user=postgres password=example") as conn:
        conn.execute(create_table_statement)


def calculate_metrics_postgresql(curr):
    value1 = rand.randint(0, 1000)
    value2 = str(uuid.uuid4())
    value3 = rand.random()

    curr.execute(
        "insert into metric_name(timestamp, value1, value2, value3) values (%s, %s, %s, %s)",
        (datetime.datetime.now(), value1, value2, value3)
    )


def main():
    prep_db()
    last_send = datetime.datetime.now() - datetime.timedelta(seconds=10)
    with psycopg.connect("host=localhost port=5432 dbname=test user=postgres password=example", autocommit=True) as conn:
        for i in range(0, 100):
            calculate_metrics()
            with conn.cursor() as curr:
                calculate_metrics_postgresql(curr)
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
