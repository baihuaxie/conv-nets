"""
utilities for dataset inspection stage
"""
import pickle
import os
import os.path as op

import matplotlib.pyplot as plt
import numpy as np
import torch

global meta_mapping
meta_mapping = {
    'CIFAR10': 'cifar-10-batches-py/batches.meta',
    'CIFAR100': 'cifar-100-python/meta'
}


from bisect import bisect_left

class discrete_cdf:
    def __init__(self, data):
        self._data = data # must be sorted
        self._data_len = float(len(data))

    def __call__(self, point):
        return (len(self._data[:bisect_left(self._data, point)]) /
                self._data_len)


def get_labels_counts(dataloader, num_classes):
    """
    Return label counts for all samples in the dataloader

    Args:
        dataloader: (DataLoader object)
        num_classes: (int) number of classes

    Returns:
        counts: (np.ndarray) a numpy array of integers; counts[i] represents counts of
                samples which have the label indexed by i in the data set

    Notes:
    - this function is for label statistics, e.g., cdf plots
    - labels must be integer id's in the dataloader
    """
    counts = np.zeros(num_classes)
    for _, (_, labels_batch) in enumerate(dataloader):
        for label in labels_batch.tolist():
            # label must be an integer id
            assert(isinstance(label, int)), "label {} is not indexed!".format(label)
            counts[label-1] += 1

    return counts


def get_classes(dataset, datadir):
    """
    return class names from dataset meta file as a list of strings
    """
    try:
        meta_path = op.join(datadir, meta_mapping[dataset])
    except KeyError:
        raise "dataset {} meta path not registered".format(dataset)

    assert op.isfile(meta_path), "No meta file found at {} for dataset {}".format( \
        meta_path, dataset)
    with open(meta_path, 'rb') as fo:
        dct = pickle.load(fo, encoding='ASCII')
    for key, value in dct.items():
        if 'label' in key and isinstance(value, (list, tuple)):
            return value
    raise ValueError("labels not found!")


def show_images(img):
    """
    print images

    Args:
        img: (np.ndarray or tensor) images
    """
    if isinstance(img, torch.Tensor):
        npimg = img.numpy()
    elif isinstance(img, np.ndarray):
        npimg = img
    else:
        raise TypeError("Image type {} not recognized".format(type(img)))
    # assumes npimg shape = CxHxW; transpose to HxWxC
    plt.imshow(np.transpose(npimg, (1, 2, 0)))


def show_labelled_images(img, labels, classes, nrows=8, ncols=8, savepath=None):
    """
    print images in a grid with actual labels as image titles

    Args:
        img: (tensor or np.ndarray) images; shape = BxCxHxW
        labels: (tensor or np.ndarray) label indices; shape = Bx1
        classes: (list of str) a list of strings for class names
        nrows: (int) # of rows in the grid; default=8
        ncols: (int) # of cols in the grid; default=8
        savepath: (str) path to save figures

    Note:
    - by default, # of grids to be saved = B / (nrows * ncols)
    """
    if isinstance(img, torch.Tensor):
        npimg = img.numpy()
    elif isinstance(img, np.ndarray):
        npimg = img
    else:
        raise TypeError("Image type {} not recognized".format(type(img)))

    if savepath is None:
        # by default set current working directory as savepath
        savepath = os.getcwd()

    grid_sz = ncols * nrows
    fig = plt.figure(figsize=(ncols*1.5, nrows*1.5))
    for idx in range(0, npimg.shape[0]):
        ax = fig.add_subplot(nrows, ncols, idx % grid_sz + 1, xticks=[], yticks=[])
        # add image
        show_images(npimg[idx])
        # add label
        try:
            ax.set_title(classes[int(labels[idx].item())])
        except IndexError:
            raise "label index {} out of range for {} number of \
                classes".format(labels[idx], len(classes))
        # save figure when current grid is full or when end of loop reached
        # create a new fig object once current grid is full
        if (idx + 1) % grid_sz == 0 or idx == npimg.shape[0]-1:
            fig.subplots_adjust(hspace=0.5)
            plt.savefig(savepath + "_{}.png".format(idx // grid_sz))
            plt.show()
            if (idx + 1) % grid_sz == 0:
                fig = plt.figure(figsize=(ncols*1.5, nrows*1.5))
