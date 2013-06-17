#!/usr/bin/env python

import copy
import os
import sys
import time

# How many fail per second we can accept
ALERT = "10.00"

NAME_PREFIX = 'varnish_'
PARAMS = {
    'stats_command': 'varnishstat -1'
}
METRICS = {
    'time': 0,
    'data': {}
}
LAST_METRICS = copy.deepcopy(METRICS)
METRICS_CACHE_MAX = 5

DESC_SKEL = {
    'name': 'XXX',
    'call_back': 'XXX',
    'time_max': 60,
    'value_type': 'float',
    'format': '%f',
    'units': 'XXX',
    'slope': 'both',  # zero|positive|negative|both
    'description': 'XXX',
    'groups': 'varnish',
}


def create_desc(skel, prop):
    desc = skel.copy()
    for key, value in prop.iteritems():
        desc[key] = value
    return desc


def get_metrics():
    global METRICS, LAST_METRICS

    if (time.time() - METRICS['time']) > METRICS_CACHE_MAX:

        # get raw metric data
        io = os.popen(PARAMS['stats_command'])

        # convert to dict
        metrics = {}
        for line in io.readlines():
            values = line.split()[:2]
            try:
                metrics[values[0]] = int(values[1])
            except ValueError:
                metrics[values[0]] = 0

        # update cache
        LAST_METRICS = copy.deepcopy(METRICS)
        METRICS = {
            'time': time.time(),
            'data': metrics
        }

    return [METRICS, LAST_METRICS]


def get_value(name):

    """ Return a value for the requested metric """

    metrics = get_metrics()[0]

    name = name[len(NAME_PREFIX):]  # remove prefix from name
    try:
        result = metrics['data'][name]
    except StandardError:
        result = 0

    return result


def get_delta(name):
    """ Return change over time for the requested metric """

    curr_metrics, last_metrics = get_metrics()

    # get delta
    name = name[len(NAME_PREFIX):]  # remove prefix from name
    try:
        delta_name = curr_metrics['data'][name]
        delta_metrics = last_metrics['data'][name]
        delta_time = curr_metrics['time'] - last_metrics['time']
        delta = float(delta_name - delta_metrics) / delta_time
        if delta < 0:
            print "Less than 0"
            delta = 0
    except StandardError:
        delta = 0

    return delta


def metric_init(lparams):
    # Initialize metric descriptors

    global PARAMS, DESC_SKEL

    # set parameters
    for key in lparams:
        PARAMS[key] = lparams[key]

    descriptors = []

    descriptors.append(create_desc(DESC_SKEL, {
        "name": NAME_PREFIX + 'backend_fail',
        "call_back": get_delta,
        "units": "fail/s",
        "description": "Backend conn. failures",
    }))

    return descriptors

if __name__ == '__main__':
    descriptors = metric_init(PARAMS)
    i = 0
    while i < 3:
        for desc in descriptors:
            back_fail = ('%f') % desc['call_back'](desc['name'])
            i = i + 1
            time.sleep(6)
            if i == 3:
                if back_fail >= ALERT:
                    print "CRITICAL: Check Varnish backend"
                    sys.exit(2)
                else:
                    print "OK: Everything is fine!"
                    sys.exit(0)
