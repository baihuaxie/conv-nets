"""
utilities for dataset inspection
"""
import pickle
import os.path as op

import matplotlib.pyplot as plt
import numpy as np
import torch

global meta_mapping
meta_mapping = {
    'CIFAR10': 'cifar-10-batches-py/batches.meta',
    'CIFAR100': 'cifar-100-python/meta'
}

def get_classes(dataset, datadir):
    """
    return class names from dataset meta file as a list of strings
    """
    meta_path = op.join(datadir, meta_mapping[dataset])
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


def show_labelled_images(img, labels, classes, nrows=8, ncols=8):
    """
    print images in a grid with actual labels as image titles

    Args:
        img: (tensor or np.ndarray) images; shape = BxCxHxW
        labels: (tensor or np.ndarray) label indices; shape = Bx1
        classes: (list of str) a list of strings for class names
        nrows: (int) # of rows in the grid; default=8
        ncols: (int) # of cols in the grid; default=8

    Note:
    - by default, # of grids to be saved = B / (nrows * ncols)
    """
    if isinstance(img, torch.Tensor):
        npimg = img.numpy()
    elif isinstance(img, np.ndarray):
        npimg = img
    else:
        raise TypeError("Image type {} not recognized".format(type(img)))

    grid_sz = ncols * nrows
    fig = plt.figure(figsize=(nrows*1.5, ncols*1.5))
    for idx in range(0, npimg.shape[0]):
        ax = fig.add_subplot(nrows, ncols, idx % grid_sz + 1, xticks=[], yticks=[])
        # add image
        show_images(npimg[idx])
        # add label
        try:
            ax.set_title(classes[int(labels[idx].item())])
        except IndexError:
            raise("label index {} out of range for {} number of \
                classes".format(labels[idx], len(classes)))
        # create a new fig object once grid_sz is reached
        if (idx + 1) % grid_sz == 0:
            fig.subplots_adjust(hspace=1)
            plt.show()
            fig = plt.figure(figsize=(nrows*1.5, ncols*1.5))
    plt.show()
    





