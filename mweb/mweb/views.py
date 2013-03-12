
from django.http      import HttpResponse
from django.template  import Context, loader
from django.shortcuts import render
from django.http import Http404

import jsonrpclib
import json
import string
import time
import datetime

jsonrpclib.config.version = 1.0

DATA_SERVER_ENDPOINT  = 'http://localhost:7080'
DATA_PROTOCOL_VERSION = '1'

class Event(object):

    ALIVE   = "ALIVE"
    MISSING = "MISSING"

    def __init__(self, attrs):
        self.timestamp = attrs['timestamp']
        self.state     = attrs['state']

class Worker(object):

    HEALTHY  = "HEALTHY"
    IMPAIRED = "IMPAIRED"
    MISSING  = "MISSING"

    TIME_FMT = "%Y-%m-%d %H:%M:%S %Z"

    #
    # Construct a worker with a list of events and identifying attributes
    def __init__(self, events, attrs):
        self.events    = events
        self.worker_id = attrs['worker_id']
        # URI-safe form of worker_id
        self.urlname   = string.replace(attrs['worker_id'], '-', '_')
        self.hostname  = attrs['hostname']
        self.pid       = attrs['pid']

        self.analyze_health()

    def analyze_health(self):
        # Inspect the most recent event to see whether Worker is missing or not
        cur = self.events[-1]
        if cur.state == Event.MISSING:
            self.health = Worker.MISSING
            self.missing_time_str     = datetime.datetime.utcfromtimestamp(cur.timestamp).strftime(Worker.TIME_FMT)
            self.missing_duration_str = self.format_missing_duration(time.time() - cur.timestamp)
        else:
            count = 0
            for ev in self.events:
                if ev.state == Event.MISSING:
                    count = count + 1
            if count > 0:
                self.health        = Worker.IMPAIRED
                self.missing_count = count
            else:
                self.health        = Worker.HEALTHY
                self.missing_count = 0

    def format_missing_duration(self, interval):
        # extract hour, minute, second components from the given interval, and format appropriately
        hh, mm = divmod(interval, 3600)
        mm, ss = divmod(mm, 60)
        if not hh and not mm:
            interval_str = "%02ds" % ss
        elif not hh:
            interval_str = "%02dm%02ds" % (mm, ss)
        else:
            interval_str = "%dh%02dm%02ds" % (hh, mm, ss)
        return interval_str

# Represents a physical host
class Host(object):

    # Ivars:
    #
    #   hostname: the UNIX hostname for this host
    #   workers:  A list of Worker objects running on this host
    #

    def __init__(self, hostname, workers):
        self.hostname = hostname
        self.workers  = workers

class System(object):

    # Ivars:
    #
    #   workers: list of workers operating in this system
    #   hosts:   list of hosts on which workers are running
    #

    # Parse the JSON tree and convert into a tree of System, Host, Worker, event objects
    #
    # Returns: A list of System objects, each containing a list of Workers and
    # a list of Hosts. In turn, each Host object also contains a list of Workers.
    #
    @classmethod
    def parse(cls, data):
        systems = []
        for system_id, wkrs in data.iteritems():
            workers_by_host = {}
            workers = []
            for wkr_attrs in wkrs.values():
                events = []
                for ev in wkr_attrs['events']:
                   events.append(Event(ev))
                wkr = Worker(events, wkr_attrs['record'])
                workers.append(wkr)
                if not workers_by_host.has_key(wkr.hostname):
                    workers_by_host[wkr.hostname] = [ wkr ]
                else:
                    workers_by_host[wkr.hostname].append(wkr)
            hosts = []
            for hostname, wkrs in workers_by_host.iteritems():
                 hosts.append(Host(hostname, wkrs))
            systems.append(System(system_id, hosts, workers))
        return systems

    def __init__(self, system_id, hosts, workers):
        self.system_id = system_id
        self.urlname   = string.replace(system_id, '-', '_')
        self.hosts     = hosts
        self.workers   = workers

    def worker_count(self):
        return len(self.workers)

    def host_count(self):
        return len(self.hosts)

class DataModel(object):

    def __init__(self):
        self._data_client = jsonrpclib.Server(DATA_SERVER_ENDPOINT)

    def get_all_system_state(self):
        data = self._data_client.get_state(DATA_PROTOCOL_VERSION)
        return System.parse(data)

    def dump_json(data):
        return json.dumps(data, sort_keys=True, indent=4)

#
# Homepage view
#
def home(request):
    return render(request, 'index.html', {})

#
# View: /systems/
#
# Makes a call to the data server to retrieve systems state
# and renders the appropriate template
#
def systems(request):
    model = DataModel()
    systems = model.get_all_system_state()
    params = { 'systems' : systems }

    return render(request, 'systems.html', params)

#
# View: /hosts/
#
def hosts(request):
    return render(request, 'hosts.html', {})

#
# View: /resources/
#
def resources(request):
    return render(request, 'resources.html', {})

#
# View: /system/
#
def system(request):
    return render(request, 'hosts.html', {})

#
# View: /system/{system_id}/{worker_id}/
#
def worker(request, system_id, worker_id):
    return render(request, 'hosts.html', {})
