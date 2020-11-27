"""
test dataset inspection utilities
"""

import pytest
import matplotlib.pyplot as plt

from torch.utils.data import DataLoader
from torchvision.transforms import transforms
from torchvision.utils import make_grid
import torchvision.datasets as ds

from common.data_loader import select_n_random
from common.utils_dataset_inspection import show_images, \
    show_labelled_images, get_classes


# keyword arguments for Dataloader
kwargs = {
    "batch_size": 32,
    "num_workers": 4,
    "pin_memory": False,
    "shuffle": True
}


@pytest.fixture(params=['CIFAR100'])
def dataset(request):
    return request.param

@pytest.fixture(params=['../../data/'])
def datadir(request):
    return request.param

@pytest.fixture(params=[transforms.Compose([])])
def transform(request):
    return request.param

@pytest.fixture
def datasets(dataset, datadir, transform):
    """
    load dataset into dataloader object
    """
    print(dataset)
    train_set = getattr(ds, dataset)(datadir, download=False, \
        train=True, transform=transform)
    test_set = getattr(ds, dataset)(datadir, download=False, \
        train=False, transform=transform)
    train_dl = DataLoader(train_set, **kwargs)
    test_dl = DataLoader(test_set, **kwargs)
    return train_dl, test_dl

@pytest.fixture
def classes(dataset, datadir):
    """
    """
    return get_classes(dataset, datadir)

@pytest.fixture
def select_random_train(dataset, datadir):
    """
    select n random data points from training set
    """
    return select_n_random('train', datadir, dataset, n=20)

@pytest.mark.skip()
def test_imshow(select_random_train):
    """
    print images
    """
    images, _ = select_random_train
    print(images.shape)
    # make_grid input must be BxCxHxW in shape
    img_grid = make_grid(images)
    show_images(img_grid)
    plt.show()


def test_show_labelled_images(select_random_train, classes):
    """
    """
    images, labels = select_random_train
    show_labelled_images(images, labels, classes, nrows=4, ncols=4)
    