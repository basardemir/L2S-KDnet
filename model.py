import math

import torch
import torch.nn as nn
from torch.nn import functional as F
from torch.nn.modules.module import Module


class GCN(Module):
    """
    Graph Convolutional Network
    """

    def __init__(self, in_features, out_features, bias=True):
        super(GCN, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(out_features))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1. / math.sqrt(self.weight.size(1))
        self.weight.data.uniform_(-stdv, stdv)
        if self.bias is not None:
            self.bias.data.uniform_(-stdv, stdv)

    def forward(self, input, adj):
        support = torch.mm(input, self.weight)
        output = torch.spmm(adj, support)
        if self.bias is not None:
            return output + self.bias
        else:
            return output

    def __repr__(self):
        return self.__class__.__name__ + ' (' \
               + str(self.in_features) + ' -> ' \
               + str(self.out_features) + ')'


class GCNencoder(nn.Module):
    """
    Encoder network.
    """

    def __init__(self, nfeat, nhid, nout, dropout):
        super(GCNencoder, self).__init__()

        self.dropout = dropout

        self.gc1 = GCN(nfeat, nhid)
        self.gc2 = GCN(nhid, nout)

    def forward(self, x, adj):
        x = F.relu(self.gc1(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        x = F.relu(self.gc2(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        return x


class GCNdecoder(nn.Module):
    """
    Decoder network.
    """

    def __init__(self, nfeat, nhid, nout, dropout):
        super(GCNdecoder, self).__init__()

        self.dropout = dropout

        self.gc1 = GCN(nfeat, nhid)
        self.gc2 = GCN(nhid, nout)


    def forward(self, x, adj):
        x = F.relu(self.gc1(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        x = F.relu(self.gc2(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        return x


class Discriminator(nn.Module):
    """
    Discriminator network with GCN.
    """

    def __init__(self, input_size, output_size, dropout):
        super(Discriminator, self).__init__()

        self.dropout = dropout

        self.gc1 = GCN(input_size, 32)
        self.gc2 = GCN(32, 16)
        self.gc3 = GCN(16, output_size)

    def forward(self, x, adj):
        x = F.relu(self.gc1(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        x = F.relu(self.gc2(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        a = self.gc3(x, adj)
        x = a.view(a.shape[0])
        return F.sigmoid(x), F.softmax(x, dim=0)


class Teacher(nn.Module):
    """
    Teacher Network that consist of encoder and decoder
    """
    def __init__(self, nfeat, nhid1, nhid2, nhid3, nhid4, dropout):
        super(Teacher, self).__init__()

        self.dropout = dropout

        self.encoder = GCNencoder(nfeat, nhid1, nhid2, dropout)
        self.decoder = GCNdecoder(nhid2, nhid3, nhid4, dropout)

    def forward(self, x, adj):
        embedding = self.encoder.forward(x, adj)
        super_resolved_matrix = self.decoder.forward(embedding, adj)
        return embedding, super_resolved_matrix


class Student(nn.Module):
    """
    Student Network that consist of encoder and decoder
    """
    def __init__(self, nfeat, nhid1, nhid2, nhid3, nhid4, dropout):
        super(Student, self).__init__()

        self.dropout = dropout

        self.encoder = GCNencoder(nfeat, nhid1, nhid2, dropout)
        self.decoder = GCNdecoder(nhid2, nhid3, nhid4, dropout)

    def forward(self, x, adj):
        embedding = self.encoder.forward(x, adj)
        super_resolved_matrix = self.decoder.forward(embedding, adj)
        return embedding, super_resolved_matrix
