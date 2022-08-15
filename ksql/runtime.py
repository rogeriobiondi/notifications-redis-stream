
import os
import json
import logging

from threading import Thread
from time import sleep

from pytz import utc
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from kafka import KafkaConsumer

class Scheduler:
    """ PoC Scheduler """    

    # This example is using the SQLite Database but you may change the default to PostgreSQL or Redis
    # This may also be backed by memory, but the escalation will not possible without a shared common storage
    # TODO: parametrization of thread pool executors, max instances, database connection string, kafka etc. 
    jobstores = {
        # 'redis': RedisJobStore(jobs_key='dispatched_trips_jobs', run_times_key='dispatched_trips_running', host='localhost', port=6379),
        # 'postgres': SQLAlchemyJobStore(url='postgres://user:pass@server:port/db') 
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }

    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    }

    job_defaults = {
        'coalesce': True,
        'max_intances': 3
    }

    scheduler = BlockingScheduler(executors = executors, job_defaults = job_defaults, 
        jobstores = jobstores, daemon=True, timezone=utc)

    def check_msgs(self):
        """ Kafka kSQL Consumer """
        consumer = KafkaConsumer('PACKAGES_BY_SELLER', bootstrap_servers=['localhost:29092'])
        for message in consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            # print(message)
            # print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
            #                                  message.offset, message.key,
            #                                  message.value))
            if not message.value: continue  # Skip the TOMBSTONE messages
            msg = message.value.decode('utf-8')
            o = json.loads(msg) 
            job_id = str(o['ID']).strip()
            job = self.scheduler.get_job(job_id)
            if not job:
                self.scheduler.add_job(self.notify, 'interval', minutes = self.dispatch_time, id = job_id, args = [o])
                print(f"New job created for seller {job_id}...")
            else:
                self.scheduler.remove_job(job.id)
                self.scheduler.add_job(self.notify, 'interval', minutes = self.dispatch_time, id = job.id, args = [o])
                print(f"Job for seller {job_id} updated...")
            self.scheduler.print_jobs()

    def notify(self, msg):
        """ Notification function """
        # TODO: implement the notification dispatch here.
        print (f"Notification sent for seller {msg['ID']}. Packages {msg['PACKAGES']}")
        # Remove the job (runs once)
        self.scheduler.remove_job(str(msg['ID']))

    def __init__(self, type, dispatch_time):
        self.type = type
        self.dispatch_time = dispatch_time
        # If the instance is FULL (more than a RUNTIME), checks Kafka if there are packages for notification
        if self.type == 'FULL':
            check = Thread(target = self.check_msgs)
            check.start()
        # Starts the Apscheduler
        self.scheduler.start()

def main():
    """ Main function """
    LOG_LEVEL     = os.getenv('LOG_LEVEL', default=logging.INFO)  # Log Level
    INSTANCE_TYPE = os.getenv('INSTANCE_TYPE', default='FULL')    # RUNTIME or FULL
    DISPATCH_TIME = os.getenv('DISPATCH_TIME', default=5)         # Message dispatch time
    logging.basicConfig(level=LOG_LEVEL)
    sched = Scheduler(type = INSTANCE_TYPE, dispatch_time = DISPATCH_TIME); 
    
if __name__ == "__main__":
    """ Program Entry Point """
    main()