"""
    create run directories under ./experiments folder
"""

import os
import json
import argparse
from subprocess import check_call
import sys

from common.utils import Params, match_dict_by_value

PYTHON = sys.executable


# put run directories in a global list for launch script to access
global runs
runs = []

# commandline arguments; normally just use defaults
parser = argparse.ArgumentParser()
parser.add_argument('--exp_dir', default='./experiments/', \
    help='Parent directory for all experiments')
parser.add_argument('--data_dir', default='./data/imagenet/images/', help="Parent \
    directory for the dataset")
parser.add_argument('--default_dir', default='./common/', \
    help='Directory containing default parameters.json file')
parser.add_argument('--jobs_dir', default='./', \
    help='Directory containing jobs.json file')
parser.add_argument('--runmode', default='train', \
    help='main.py runmode (train or test)')
parser.add_argument('--runset', default='launch-test.json', \
    help='.json runset configuration file')


# construct a run directory name string from runset dict
def rundct_to_list(dct):
    """
    put all runset values in a dictionary (could by 3-level hierarchical) into a list object
    also convert all elements into str

    note:
    - runset dict object contain
        - key: value_dict -> where value_dict is also a dictionary; this is for parameters that
          should be distinguished in ablation studies, e.g., network, optimizer, scheduler, and
          their settings
        - key: value -> where value is not an iterable object; this is for parameters that need
          not be distinguished in ablation studies, e.g., number of epochs, etc.; this routine
          ignores such values in the returned list
    """
    assert isinstance(dct, dict)
    lst = []
    for value in dct.values():
        if isinstance(value, dict):
            for val in value.values():
                if isinstance(val, dict):
                    lst += [str(v) for v in val.values() if v is not None]
                else:
                    lst.append(str(val))
    return lst


# decorator to register run directories
def register(func):
    """
    Decorator: register a run directory returned by a call to create_job()
    """
    def _wrapper(*args, **kwargs):
        """
        inner decorator function takes arguments
        - no need to modify behaviors so no wrappers
        """
        runs.append(func(*args, **kwargs))
    return _wrapper


@register
def create_job(run_dct, defaults):
    """
    create a run directory from run_dict

    Args:
        run_dct: (dict) contains parameters for one job run
        defaults: (dict) default keyword arguments for all optimizers, schedulers, datasets, etc.
                  unless specified by run_dct, otherwise always use default keyword arguments
    Return:
        create a run directory if does not exist
        create a self-contained runset.json file under the run directory for main.py
        returns run_dir: os.path object to the directory
    """

    # create run directory
    run_dir = os.path.join(exp_dir, '_'.join(rundct_to_list(run_dct)))
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)

    # construct runset.json
    runset = {}
    runset.update({k:v for k, v in defaults.dict.items() if k not in ['data', \
        'optimizer', 'scheduler']})
    for key, value in run_dct.items():
        if key == 'data':
            data_dct = match_dict_by_value(defaults.data, 'dataset', value['dataset'])
            for k, v in value.items():
                if k != 'dataset':
                    data_dct[k].update(v)
            # data_dct['dataloader-kwargs'].update({k:v for k, v in value.items() if k != 'dataset'})
            runset.update({'data': data_dct})
        elif key == 'optimizer':
            optim_dct = match_dict_by_value(defaults.optimizer, 'type', value['type'])
            optim_dct['kwargs'].update({k:v for k, v in value.items() if k != 'type'})
            runset.update({'optimizer': optim_dct})
        elif key == 'lr':
            lr_dct = match_dict_by_value(defaults.scheduler, 'type', value['type'])
            lr_dct['kwargs'].update({k:v for k, v in value.items() if k != 'type'})
            runset.update({'scheduler': lr_dct})
        else:
            runset.update({key:value})

    # add a "kwargs" field under "model" key
    runset['model'].update({'kwargs': {}})
    # add num_classes from "data" key to "model" key
    try:
        runset['model']['kwargs'].update({'num_classes': data_dct['num_classes']})
    except KeyError:
        pass
    # save runset.json
    with open(os.path.join(run_dir, 'runset.json'), 'w') as fp:
        json.dump(runset, fp, indent=4)

    # append run directory to global list
    return run_dir


if __name__ == '__main__':
    args = parser.parse_args()
    # read parameters of all job runs from jobs.json
    json_path = os.path.join(args.jobs_dir, args.runset)
    jobs = Params(json_path)

    # read default parameters
    defaults = Params(os.path.join(args.default_dir, 'parameters.json'))

    # create parent experiment directory
    exp_dir = os.path.join(args.exp_dir, jobs.jobname)
    if not os.path.exists(exp_dir):
        os.makedirs(exp_dir)

    # save jobs.json
    jobs.save(os.path.join(exp_dir, 'jobs.json'))

    # create run directories + runset.json files
    for run_dct in jobs.experiments:
        create_job(run_dct, defaults)

    # Launch job
    for run_dir in runs:
        # launch training job with specified setting
        cmd = "{python} main.py --run_dir {run_dir} --data_dir {data_dir} \
            --run_mode {runmode}".format(python=PYTHON, run_dir=run_dir, data_dir=args.data_dir, \
                runmode=args.runmode)
        print(cmd)
        check_call(cmd, shell=True)
    