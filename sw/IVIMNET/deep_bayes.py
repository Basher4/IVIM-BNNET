from tqdm import tqdm
from typing import Optional
from tqdm import tqdm
from collections import namedtuple
from dataclasses import dataclass
import numpy as np
import copy

import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as utils

from IVIMNET.dropout import BernoulliDropout
import IVIMNET.fitting_algorithms as fit
import IVIMNET.deep as deep

MinMax = namedtuple('MinMax', ['min', 'max'])

@dataclass
class MinMax:
    min: float
    max: float
    def delta(self):
        return self.max - self.min

@dataclass
class ParamBounds:
    D:  MinMax
    f:  MinMax
    Dp: MinMax
    f0: MinMax
    Dp2: MinMax = None
    f2: MinMax = None

@dataclass
class net_params:
    """ Replicating 'optim' settings from hyperparameters.py """
    dropout:    float = 0.1
    activation: str = "relu"
    depth:      int = 2
    width:      Optional[int] = None  # Wide as number of b-values
    bounds:     ParamBounds = ParamBounds(D  = MinMax(0.0, 0.005), f  = MinMax(0.0, 0.7), # Dt, Fp
                                          Dp = MinMax(0.005, 0.2), f0 = MinMax(0.0, 2.0)) # Ds, S0

class Net(nn.Module):
    def __init__(self, bvalues: np.array, net_params: net_params, bayes_samples):
        super().__init__()

        self.bvalues = bvalues
        self.net_params = net_params
        self.net_params.width = self.net_params.width or len(bvalues)
        self.bayes_samples = bayes_samples
        self.est_params = 4     # No tri-exponential fitting and estimate S0

        if self.net_params.activation.lower() == "relu":
            activation_fn = nn.ReLU
        elif self.net_params.activation.lower() == "elu":
            activation_fn == nn.ELU

        width = len(bvalues)
        self.fc_layers = nn.ModuleList([nn.ModuleList() for _ in range(self.est_params)])
        for i in range(self.net_params.depth):
            for layer in self.fc_layers:
                layer.extend([
                    nn.Linear(width, self.net_params.width),
                    BernoulliDropout(self.net_params.dropout),
                    nn.BatchNorm1d(self.net_params.width), # Add batch normalization - default param.
                    activation_fn(),                       # Add non-linearity - default param.
                ])                

        # Parallel network to estimate each parameter separately.
        self.encoder = nn.ModuleList([nn.Sequential(*fcl, nn.Linear(self.net_params.width, 1)) for fcl in self.fc_layers])

    def forward(self, X):
        def sigm(param, bound: MinMax):
            return bound.min + torch.sigmoid(param[:, :, 0].unsqueeze(2)) * bound.delta()

        pb = self.net_params.bounds

        X_stack = torch.cat([X] * self.bayes_samples)
        paramsSamples = [enc(X_stack).reshape((self.bayes_samples, X.shape[0], 1)) for enc in self.encoder]
        del X_stack
        # params = torch.stack(paramsSamples, dim=0).mean(dim=1)
        params = paramsSamples

        Dt = sigm(params[2], pb.D)
        Fp = sigm(params[0], pb.f)
        Dp = sigm(params[1], pb.Dp)
        f0 = sigm(params[3], pb.f0)

        for t in params:
            del t

        # loss function
        X = Fp * torch.exp(-self.bvalues * Dp) + f0 * torch.exp(-self.bvalues * Dt)
        return X, Dt, (Fp/(f0+Fp)), Dp, (f0+Fp)


def learn_IVIM(X_train, bvalues, arg, epochs=1000, net_params=net_params(), stats_out=False, bayes_samples=32):
    torch.backends.cudnn.benchmark = True
    arg = deep.checkarg(arg)

    ## normalise the signal to b=0 and remove data with nans
    X_train = deep.normalise(X_train, bvalues, arg)
    bvalues = torch.FloatTensor(bvalues[:]).to(arg.train_pars.device)
    net = Net(bvalues, net_params, bayes_samples).to(arg.train_pars.device)

    criterion = nn.MSELoss(reduction='mean').to(arg.train_pars.device)
    split = int(np.floor(len(X_train) * arg.train_pars.split))
    train_set, val_set = torch.utils.data.random_split(torch.from_numpy(X_train.astype(np.float32)),
                                                       [split, len(X_train) - split])

    # train loader loads the trianing data. We want to shuffle to make sure data order is modified each epoch and different data is selected each epoch.
    trainloader = utils.DataLoader(train_set,
                                   batch_size=arg.train_pars.batch_size,
                                   shuffle=True,
                                   drop_last=True)

    # validation data is loaded here. By not shuffling, we make sure the same data is loaded for validation every time. We can use substantially more data per batch as we are not training.
    inferloader = utils.DataLoader(val_set,
                                   batch_size=min(len(val_set), 32 * arg.train_pars.batch_size),
                                   shuffle=False,
                                   drop_last=True)

    totalit = np.min([arg.train_pars.maxit, np.floor(split // arg.train_pars.batch_size)])
    batch_norm2 = np.floor(len(val_set) // (min(val_set.__len__(),32 * arg.train_pars.batch_size)))

    optimizer = optim.Adam(filter(lambda p: p.requires_grad, net.parameters()), lr=arg.train_pars.lr, weight_decay=1e-4)

    # Initialising parameters
    best = 1e16
    num_bad_epochs = 0
    loss_train = []
    loss_val = []
    # get_ipython().run_line_magic('matplotlib', 'inline')
    final_model = copy.deepcopy(net.state_dict())
    epoch = 0

    while epoch < epochs:
        print("-----------------------------------------------------------------")
        print(f"Epoch: {epoch}; Bad epochs: {num_bad_epochs}")
        # initialising and resetting parameters
        net.train()
        running_loss_train = 0.
        running_loss_val = 0.
        for i, X_batch in enumerate(tqdm(trainloader, position=0, leave=True, total=totalit), 0):
        # for i, X_batch in enumerate(trainloader, 0):
            if i > totalit:
                # have a maximum number of batches per epoch to ensure regular updates of whether we are improving
                break
            # zero the parameter gradients
            optimizer.zero_grad()
            # put batch on GPU if pressent
            X_batch = X_batch.to(arg.train_pars.device)
            ## forward + backward + optimize - we are not predicting tri exponential data.
            X_pred, del1, del2, del3, del4 = net(X_batch)
            del del1
            del del2
            del del3
            del del4
            X_pred = torch.mean(X_pred, dim=0)
            X_pred[torch.isnan(X_pred)] = 0         # removing nans and too high/low predictions to prevent overshooting
            X_pred[X_pred < 0] = 0
            X_pred[X_pred > 3] = 3
            # determine loss for batch; note that the loss is determined by the difference between
            # the predicted signal and the actual signal. The loss does not look at Dt, Dp or Fp.
            loss = criterion(X_pred, X_batch)
            del X_pred	
            # updating network
            loss.backward()
            optimizer.step()
            # total loss and determine max loss over all batches
            running_loss_train += loss.item()

        # validation is always done over all validation data
        print('Validation')
        for i, X_batch in enumerate(tqdm(inferloader, position=0, leave=True), 0):
        # for i, X_batch in enumerate(trainloader, 0):
            optimizer.zero_grad()
            X_batch = X_batch.to(arg.train_pars.device)
            # do prediction, only look at predicted IVIM signal
            # stack = torch.stack([net(X_batch)[0] for _ in range(bayes_samples)])
            # X_pred = torch.mean(stack, dim=0)
            X_pred, del1, del2, del3, del4 = net(X_batch)
            del del1
            del del2
            del del3
            del del4
            X_pred = torch.mean(X_pred, dim=0)
            X_pred[torch.isnan(X_pred)] = 0 # removing nans and too high/low predictions to prevent overshooting
            X_pred[X_pred < 0] = 0
            X_pred[X_pred > 3] = 3
            # validation loss
            loss = criterion(X_pred, X_batch)
            del X_pred
            running_loss_val += loss.item()
        # scale losses
        running_loss_train = running_loss_train / totalit
        running_loss_val = running_loss_val / batch_norm2
        # save loss history for plot
        loss_train.append(running_loss_train)
        loss_val.append(running_loss_val)

        # early stopping criteria
        if running_loss_val < best:
            print(f"Validation loss: {running_loss_val}")
            print("############### Saving good model ###############################\n")
            final_model = copy.deepcopy(net.state_dict())
            best = running_loss_val
            num_bad_epochs = 0
        else:
            num_bad_epochs += 1
            if num_bad_epochs == 10:
                print(f"Done, best val loss: {best}\n")
                break
        epoch += 1
    print("Done")

    # Restore best model
    if arg.train_pars.select_best:
        net.load_state_dict(final_model)
    del trainloader
    del inferloader
    if arg.train_pars.use_cuda:
        torch.cuda.empty_cache()

    if stats_out:
        return net, epoch, best
    return net

def predict_IVIM(data, bvalues, net, arg, signals_out=False, batch_size=256):
    arg = deep.checkarg(arg)

    ## normalise the signal to b=0 and remove data with nans
    data = deep.normalise(data, bvalues, arg)
    mylist = np.isnan(np.mean(data, axis=1))
    sels = [not i for i in mylist]
    # remove data with non-IVIM-like behaviour. Estimating IVIM parameters in these data is meaningless anyways.
    sels = sels & (np.percentile(data[:, bvalues < 50], 0.95, axis=1) < 1.3) & (
                np.percentile(data[:, bvalues > 50], 0.95, axis=1) < 1.2) & (
                       np.percentile(data[:, bvalues > 150], 0.95, axis=1) < 1.0)
    # we need this for later
    lend = len(data)
    data = data[sels]

    # tell net it is used for evaluation
    net.eval()
    # initialise parameters and data
    X  = np.array([])
    Dp = np.array([])
    Dt = np.array([])
    Fp = np.array([])
    S0 = np.array([])

    # initialise dataloader. Batch size can be way larger as we are still training.
    inferloader = utils.DataLoader(torch.from_numpy(data.astype(np.float32)),
                                   batch_size=batch_size,
                                   shuffle=False,
                                   drop_last=False)
    # start predicting
    with torch.no_grad():
        for i, X_batch in tqdm(enumerate(inferloader, 0)):
            X_batch = X_batch.to(arg.train_pars.device)
            # here the signal is predicted. Note that we now are interested in the parameters and no longer in the predicted signal decay.
            Xt, Dtt, Fpt, Dpt, S0t = net(X_batch)
            X  = np.append(X,  (Xt.cpu()).numpy())
            S0 = np.append(S0, (S0t.cpu()).numpy())
            Dt = np.append(Dt, (Dtt.cpu()).numpy())
            Fp = np.append(Fp, (Fpt.cpu()).numpy())
            Dp = np.append(Dp, (Dpt.cpu()).numpy())

    if np.mean(Dp) < np.mean(Dt):
        Dp22 = copy.deepcopy(Dt)
        Dt = copy.deepcopy(Dp)
        Dp = copy.deepcopy(Dp22)
        Fp = 1 - Fp    # here we correct for the data that initially was removed as it did not have IVIM behaviour, by returning zero

    # estimates
    Xtrue = np.asarray(X)
    Dptrue = np.zeros(lend)
    Dttrue = np.zeros(lend)
    Fptrue = np.zeros(lend)
    S0true = np.zeros(lend)
    Dptrue[sels] = Dp
    Dttrue[sels] = Dt
    Fptrue[sels] = Fp
    S0true[sels] = S0
    del inferloader
    if arg.train_pars.use_cuda:
        torch.cuda.empty_cache()

    if signals_out:
        return [Xtrue, Dttrue, Fptrue, Dptrue, S0true]
    return [Dttrue, Fptrue, Dptrue, S0true]
