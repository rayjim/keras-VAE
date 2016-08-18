from __future__ import division
from keras.layers import Input, Dense, Activation
from keras.models import Model, Sequential
import keras.backend as K
from probability_distributions import GaussianDistribution, BernoulliDistribution
from custom_batchnormalization import CustomBatchNormalization


class VAEM1(object):
    def __init__(self, in_dim=784, hid_dim=300, z_dim=50):
        self.in_dim = in_dim
        self.hid_dim = hid_dim
        self.z_dim = z_dim
        self.x = Input((self.in_dim, ))
        self.z = Input((self.z_dim, ))

        #####################
        #Define Architecture#
        #####################
        model = Sequential()
        model.add(Dense(self.hid_dim, input_dim=self.in_dim))
        model.add(CustomBatchNormalization())
        model.add(Activation('relu'))
        model.add(Dense(self.hid_dim))
        model.add(CustomBatchNormalization())
        model.add(Activation('relu'))
        mean = Sequential([model])
        mean.add(Dense(self.hid_dim))
        mean.add(CustomBatchNormalization())
        mean.add(Activation('relu'))
        mean.add(Dense(self.z_dim, activation='relu'))
        var = Sequential([model])
        var.add(Dense(self.hid_dim))
        var.add(CustomBatchNormalization())
        var.add(Activation('relu'))
        var.add(Dense(self.z_dim, activation='sigmoid'))
        self.q_z_x = GaussianDistribution(self.z, givens=[self.x], mean_model=mean, var_model=var)

        model = Sequential()
        model.add(Dense(self.hid_dim, input_dim=self.z_dim))
        model.add(CustomBatchNormalization())
        model.add(Activation('relu'))
        model.add(Dense(self.hid_dim))
        model.add(CustomBatchNormalization())
        model.add(Activation('relu'))
        model.add(Dense(self.in_dim, activation='sigmoid'))
        self.p_x_z = BernoulliDistribution(self.x, givens=[self.z], model=model)

        ########################
        #sample and reconstruct#
        ########################
        self.mean, self.var = self.q_z_x.get_params(givens=[self.x])
        self.sampling_z = self.q_z_x.sampling(givens=[self.x])
        self.reconstruct_x = self.p_x_z.sampling(givens=[self.sampling_z])

    def cost(self, inputs, output):
        self.KL = 1/2*K.mean(K.sum(1+K.log(self.var)-self.mean**2-self.var, axis=1))
        self.logliklihood = self.p_x_z.logliklihood(self.x, givens=[self.sampling_z])
        self.lower_bound = self.KL+self.logliklihood
        self.lossfunc = -self.lower_bound
        return self.lossfunc

    def training_model(self):
        model = Model(input=self.x, output=self.reconstruct_x)
        return model

    def encoder(self):
        model = Model(input=self.x, output=self.mean)
        return model

    def decoder(self):
        decode = self.p_x_z.sampling(givens=[self.z])
        model = Model(input=self.z, output=decode)
        return model
