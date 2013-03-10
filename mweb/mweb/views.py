
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

VERSION = '1'

class Event(object):

    ALIVE   = 0
    MISSING = 1

    def __init__(self, attrs):
        self.timestamp = attrs['timestamp']
        self.state     = attrs['state']

class Worker(object):

    HEALTHY  = 0
    IMPAIRED = 1
    MISSING  = 2

    def __init__(self, events, attrs):
        self.events    = events
        self.worker_id = attrs['worker_id']
        self.urlname   = string.replace(attrs['worker_id'], '-', '_')
        self.hostname  = attrs['hostname']
        self.pid       = attrs['pid']

        self.analyze_health()

    def analyze_health(self):

        # set health to one of HEALTHY, IMPAIRED, MISSING
        cur = self.events[-1]
        if cur.state == Event.MISSING:
            self.health = Worker.MISSING
            period = time.time() - cur.timestamp
            m, s = divmod(period,60)
            h, m = divmod(m,60)
            if not (h and m):
                self.missing_time = "%02ds" % s
            elif not h:
                self.missing_time = "%02dm%02ds" % (m, s)
            else:
                self.missing_time = "%dh%02dm%02ds" % (h, m, s)
            self.missing_time_abbr =  datetime.datetime.utcfromtimestamp(cur.timestamp).strftime("%Y-%m-%d %H:%M:%S %Z")

        else:
            self.health = Worker.HEALTHY
            self.missing_count = 0
            for ev in self.events:
                if ev.state == Event.MISSING:
                    self.missing_count = self.missing_count + 1
                    if self.health != Worker.IMPAIRED:
                        self.health = Worker.IMPAIRED



class Host(object):

    def __init__(self, hostname, workers):
        self.hostname = hostname
        self.workers = workers

class System(object):

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


def home(request):
    server = jsonrpclib.Server('http://localhost:7080')
    data = server.get_state(VERSION)
    return render(request, 'index.html', { 'data' : json.dumps(data, sort_keys=True, indent=4) })

def systems(request):
    server = jsonrpclib.Server('http://localhost:7080')
    data = server.get_state(VERSION)
    systems = System.parse(data)
    return render(request, 'systems.html', { 'systems' : systems, 'data' : 4 })

def hosts(request):
    return render(request, 'hosts.html', { 'data' : 'foo' })

def resources(request):
    return render(request, 'resources.html', { 'data' : 'foo' })

def system(request):
    return render(request, 'hosts.html', { 'data' : 'foo' })

def worker(request, system_id, worker_id):
    return render(request, 'hosts.html', { 'data' : 'foo' })
