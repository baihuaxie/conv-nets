"""
    Classes and functions for training
"""

import os
from abc import abstractmethod

import torch
import torch.optim as optim

from common.utils import print_net_summary
from common.objectives import loss_fn, metrics
from model.build_models import get_network_builder


class Trainer(object):
    """
    A trainer object to provide launch interface for training / evaluation flows

    Trainer() contains a collection of instances:
    - model
    - optimizer
    - learning rate scheduler
    - metrics
    - loss function
    """
    def __init__(self, params, seed=200, run_dir=None):
        """
        Constructor

        Args:
            params: (Params object) a dict-like object with the runset parameters
            seed: (int) random manual seed
            run_dir: (str) directory for storing output files
        """
        # set run directory
        if run_dir is None:
            self.run_dir = os.getcwd()
        assert os.path.exists(run_dir), "Directory {} does not exist!".format(run_dir)
        self.run_dir = run_dir

        # get keyword parameters for model (if any)
        try:
            model_kwargs = params.model['kwargs']
        except KeyError:
            model_kwargs = {}
            print("Model keyword argument is not specified!")
        # get keyword parameters for optimizer and scheduler
        optim_type = params.optimizer['type']
        optim_kwargs = params.optimizer['kwargs']
        lr_type = params.scheduler['type']
        lr_kwargs = params.scheduler['kwargs']

        # get device
        self.cuda = torch.cuda.is_available()
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

        # set random seed for reproducible experiments
        torch.manual_seed(seed)
        if self.cuda:
            torch.cuda.manual_seed(seed)

        # build model
        self.model = get_network_builder(params.model['network'])(**model_kwargs).to(self.device)

        # build the optimizer
        self.optimizer = getattr(optim, optim_type)(self.model.parameters(), **optim_kwargs)

        # build learning rate scheduler
        self.scheduler = getattr(optim.lr_scheduler, lr_type)(self.optimizer, **lr_kwargs)

        # get loss function -> refactor loss_fn.py into registry
        self.loss_fn = loss_fn

        # get metrics -> refactor metrics.py into registry
        self.metrics = metrics


    def net_summary(self, x):
        """
        Get a summary for blocks, layers and dimensions in the network

        Args:
            x: (torch.tensor) input data
        """
        x = x.to(self.device)
        # write architecture to log file using torchsummary package
        print_net_summary(self.run_dir+'/net_summary.log', self.model, x)

    
    @abstractmethod
    def train(self):
        """
        Abstract method to run training
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(self):
        """
        Abstract method to evaluate a pretrained model
        """

    @abstractmethod
    def save(self):
        """
        Save a checkpoint of (model, optimizer, lr_scheduler)
        """

    @abstractmethod
    def load(self):
        """
        Load a checkpoint of (model, optimizer, lr_scheduler) from .pth file
        """