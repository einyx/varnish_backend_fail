#!/usr/bin/env python

import os
import sys
import time
import copy

""" How many fail per second we can accept """
alert = "10.00"

NAME_PREFIX = 'varnish_'
PARAMS = {
    'stats_command' : 'varnishstat -1'
}
METRICS = {
    'time' : 0,
    'data' : {}
}
LAST_METRICS = copy.deepcopy(METRICS)
METRICS_CACHE_MAX = 5

def create_desc(skel, prop):
    d = skel.copy()
    for k,v in prop.iteritems():
        d[k] = v
    return d


def get_metrics():
    """Return metrics"""
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
    """Return a value for the requested metric"""

    metrics = get_metrics()[0]

    name = name[len(NAME_PREFIX):] # remove prefix from name
    try:
        result = metrics['data'][name]
    except StandardError:
        result = 0

    return result


def get_delta(name):
    """Return change over time for the requested metric"""

    # get metrics
    [curr_metrics, last_metrics] = get_metrics()

    # get delta
    name = name[len(NAME_PREFIX):] # remove prefix from name
    try:
        delta = float(curr_metrics['data'][name] - last_metrics['data'][name])/(curr_metrics['time'] - last_metrics['time'])
        if delta < 0:
            print "Less than 0"
            delta = 0
    except StandardError:
        delta = 0

    return delta


def metric_init(lparams):
    """Initialize metric descriptors"""

    global PARAMS, Desc_Skel

    # set parameters
    for key in lparams:
        PARAMS[key] = lparams[key]

    # define descriptors
    time_max = 60

    Desc_Skel = {
        'name'        : 'XXX',
        'call_back'   : 'XXX',
        'time_max'    : 60,
        'value_type'  : 'float',
        'format'      : '%f',
        'units'       : 'XXX',
        'slope'       : 'both', # zero|positive|negative|both
        'description' : 'XXX',
        'groups'      : 'varnish',
        }

    descriptors = []

    descriptors.append( create_desc(Desc_Skel, {
                "name"       : NAME_PREFIX + 'backend_fail',
                "call_back"  : get_delta,
                "units"      : "fail/s",
                "description": "Backend conn. failures",
                }))

    return descriptors


def metric_cleanup():
    """Cleanup"""

    pass


# the following code is for debugging and testing
if __name__ == '__main__':
    descriptors = metric_init(PARAMS)
    i=0
    while i < 3:
    	for d in descriptors:
 		back_fail = ('%f') % d['call_back'](d['name']) 
		i= i+1
		print (back_fail)
		time.sleep(6)
		if i == 3:
			if back_fail >= alert:
				print "CRITICAL: Check Varnish backend"
				sys.exit(2)
			else:
				print "OK: Everything is fine!"
				sys.exit(0)

