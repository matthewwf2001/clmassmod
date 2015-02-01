#######################
# Fit a model which is lognorm intrinsic scatter and linear norm noise
########################

import glob, cPickle, os
import numpy as np
import pymc
import consolidate_fits
import deconvolvedlognormtools as dlntools
import varcontainer
import pymc_mymcmc_adapter as pma
import scipy.stats
import nfwutils, nfwfit, nfwnoise
import fitmodel

########################

def loadMCMCChains(chaindir, simtype, simreader, massedges=None, massbin=None, thin=1):

    nfwutils.global_cosmology.set_cosmology(simreader.getCosmology())

    idpattern = consolidate_fits.idpatterns[simtype]

    answers = cPickle.load(open('{0}_answers.pkl'.format(simtype), 'rb'))


        
    halos = []

    for chainfile in glob.glob('%s/*.out' % chaindir):

        filebase = os.path.basename(chainfile)

        match = idpattern.match(filebase)
        

        try:
            haloid = int(match.group(1))
        except AttributeError as e:
            print filebase
            raise e
        except ValueError:
            haloid = match.group(1)

        try:
            truth = answers[haloid]
        except KeyError:
            print 'Failure at {0}'.format(output)
            raise

        if massedges is not None \
                and massbin is not None \
                and (truth['m200'] < massedges[massbin] \
                         or truth['m200'] >= massedges[massbin+1]):
                continue


        with open(chainfile, 'rb') as input:
            chain = cPickle.load(input)

        m200s = np.array(chain['m200'][200::thin])*nfwutils.global_cosmology.h
        
        


        halos.append(dict(id = haloid,
                          true_m200 = truth['m200'],
                          measured_m200s = m200s))

    print 'Num Halos: ', len(halos)
                         
    return halos


#######################

def loadPDFs(pdfdir, simtype, simreader, massedges=None, massbin=None):

    nfwutils.global_cosmology.set_cosmology(simreader.getCosmology())

    idpattern = consolidate_fits.idpatterns[simtype]

    answers = cPickle.load(open('{0}_answers.pkl'.format(simtype), 'rb'))


        
    halos = []

    for pdffile in glob.glob('%s/*.out' % pdfdir):

        filebase = os.path.basename(chainfile)

        match = idpattern.match(filebase)
        

        try:
            haloid = int(match.group(1))
        except AttributeError as e:
            print filebase
            raise e
        except ValueError:
            haloid = match.group(1)

        try:
            truth = answers[haloid]
        except KeyError:
            print 'Failure at {0}'.format(output)
            raise

        if massedges is not None \
                and massbin is not None \
                and (truth['m200'] < massedges[massbin] \
                         or truth['m200'] >= massedges[massbin+1]):
                continue


        with open(chainfile, 'rb') as input:
            masses, pdf = cPickle.load(input)
        
        

        halos.append(dict(id = haloid,
                          true_m200 = truth['m200'],
                          masses = masses,
                          pdf = pdf))

    print 'Num Halos: ', len(halos)
                         
    return halos




#######################

def posteriorPredictivePDFs(logmu, logsigma, mtrues, config, nmlsamples=5, masses=np.arange(-5e14, 5e15, 1e13), beta = 0.28):

    if config.binspacing == 'linear':
        binedges = np.linspace(config.minradii, config.maxradii, config.nbins+1)
    else:
        binedges = np.logspace(np.log10(config.minradii), np.log10(config.maxradii), config.nbins+1)
    

    fitter = nfwfit.buildFitter(config)
    fitter.model.setData(beta, beta**2, config.targetz)

    if masses is None:
        doMaxlike=True
        maxlikes = np.zeros((nclusters, nmlsamples))
    else:
        doMaxlike = False
        nmasses = len(masses)
        pdfs = np.zeros((nclusters, nmlsamples, nmasses))

    nclusters = len(mtrues)

    for i in range(nclusters):
        mls = np.exp(logmu + np.log(mtrues[i]) + np.exp(logsigma)*np.random.standard_normal(nmlsamples))
        profile_rmpcs, shearprofiles, shearerrprofiles = nfwnoise.createClusterSet(config,
                                                                                   mls,
                                                                                   config.targetz,
                                                                                   binedges,
                                                                                   beta,
                                                                                   config.nperarcmin,
                                                                                   config.shapenoise,
                                                                                   concens = 4.*np.ones(nmlsamples))

        for j in range(nmlsamples):

            if doMaxlike is True:
                maxlikes[i,j] = modelfitter.minChisqMethod(profile_rmpcs[j], 
                                                           shearprofiles[j], 
                                                           shearerrprofiles[j], 
                                                           beta, beta**2, config.targetz)[0]*fitter.model.massScale

            else:


                modelfitter = fitmodel.FitModel(profile_rmpcs[j], 
                                                shearprofiles[j], 
                                                shearerrprofiles[j], 
                                                fitter.model,
                                                guess = fitter.model.guess())


                for k, mass in enumerate(masses):
                
                    pdfs[i,j,k] = modelfitter.statfunc(modelfitter.ydata,
                                                       modelfitter.yerr,
                                                       modelfitter.model(modelfitter.xdata,
                                                                         mass / fitter.model.massScale))



    if doMaxlike:
        return maxlikes
    else:
        pdfs = np.exp(pdfs - np.max(pdfs))
        return pdfs
    
                
#####################


def buildPDFModel(halos):

    massnorm = 1e15

    parts = {}

    parts['logmu'] = pymc.Uniform('logmu', -1., 1.)
    parts['logsigma'] = pymc.Uniform('logsigma', np.log(1e-2), np.log(10))

    @pymc.deterministic(trace=True)
    def sigma(logsigma = parts['logsigma']):
        return np.exp(logsigma)
    
    parts['sigma'] = sigma

    masses = halos[0]['masses']
    posmasses = masses[masses >= 0]
    nmasses = len(posmasses)
    deltamasses = posmasses[1:] - posmasses[:-1]


    nclusters = len(halos)

    delta_logmls = np.zeros((nclusters, nmasses))
    pdfs = np.zeros((nclusters, nmasses))

    for i in range(nclusters):

        delta_logmls[i,:] = np.log(posmasses) - np.log(halos[i]['true_m200'])
        pdfs[i,:] = halos[i]['pdf'][masses>=0]

    

    @pymc.observed
    def data(value = 0., ml_ints = posmasses/massnorm, deltamasses = deltamasses/massnorm,
             delta_logmls = delta_logmls, pdfs = pdfs,
             logmu = parts['logmu'], sigma = parts['sigma']):

        return dlntools.mcmcloglinearlike(ml_ints = ml_ints,
                                          deltamasses = deltamasses,
                                          delta_logmls = delta_logmls,
                                          pdfs = pdfs,
                                          logmu = logmu,
                                          sigma = sigma)
    parts['data'] = data

    return parts


        
                                                                                   
        
        
    

########################

def buildMCMCModel(halos, maxsamples = 200):

    massnorm = 1e15

    parts = {}

    parts['logmu'] = pymc.Uniform('logmu', -1., 1.)
    parts['logsigma'] = pymc.Uniform('logsigma', np.log(1e-2), np.log(10))

    @pymc.deterministic(trace=True)
    def sigma(logsigma = parts['logsigma']):
        return np.exp(logsigma)
    
    parts['sigma'] = sigma

    nclusters = len(halos)
    ml_ints = np.zeros((nclusters, maxsamples))
    delta_logmls = np.zeros((nclusters, maxsamples))
    ngoodsamples = np.zeros(nclusters, dtype=np.int)
    for i in range(nclusters):
        m200s = halos[i]['measured_m200s']
        positivem200s = m200s[m200s > 0]
        navailablesamples = len(positivem200s)
        takesamples = min(navailablesamples, maxsamples)
        if navailablesamples < 25:
            print 'Need more samples: ', halos[i]['id'], navailablesamples

        ml_ints[i,:takesamples] = np.random.permutation(positivem200s)[:takesamples]
        delta_logmls[i,:takesamples] = np.log(ml_ints[i,:takesamples]) - np.log(halos[i]['true_m200'])
        ngoodsamples[i] = takesamples

    

    @pymc.observed
    def data(value = 0., ml_ints = ml_ints/massnorm, delta_logmls = delta_logmls, ngoodsamples = ngoodsamples,
             logmu = parts['logmu'], sigma = parts['sigma']):

        return dlntools.mcmcloglinearlike(ml_ints = ml_ints,
                                          delta_logmls = delta_logmls,
                                          ngoodsamples = ngoodsamples,
                                          logmu = logmu,
                                          sigma = sigma)
    parts['data'] = data

    return parts


    

########################


def buildModel(mlens, merr, mtrue, nsamples = 150, noisefloor = False):

    massnorm = 1e15

    if noisefloor is True:
        merr = np.maximum(np.sqrt(merr**2 + (0.2*mtrue)**2), 0.1*np.abs(mlens))

    parts = {}

    parts['logmu'] = pymc.Uniform('logmu', -1., 1.)
    parts['logsigma'] = pymc.Uniform('logsigma', np.log(1e-4), np.log(10))

    @pymc.deterministic(trace=True)
    def sigma(logsigma = parts['logsigma']):
        return np.exp(logsigma)
    
    parts['sigma'] = sigma

    nclusters = len(mlens)
    ml_ints = np.zeros((nclusters, nsamples))
    delta_logmls = np.zeros((nclusters, nsamples))
    for i in range(nclusters):
        a, b = (0. - mlens[i]) /merr[i], (1e17 - mlens[i]) / merr[i]
        ml_ints[i,:] = mlens[i] + merr[i]*scipy.stats.truncnorm.rvs(a,b,size=nsamples)
        delta_logmls[i,:] = np.log(ml_ints[i,:]) - np.log(mtrue[i])

    

    @pymc.observed
    def data(value = 0., ml_ints = ml_ints/massnorm, delta_logmls = delta_logmls, 
             logmu = parts['logmu'], sigma = parts['sigma']):

        return dlntools.loglinearlike(ml_ints = ml_ints,
                                      delta_logmls = delta_logmls,
                                      logmu = logmu,
                                      sigma = sigma)
    parts['data'] = data

    return parts


#######################################

def buildOutlierModel(mlens, merr, mtrue, nsamples = 150, outlierfactor=100):

    massnorm = 1e15

    parts = {}

    parts['logmu'] = pymc.Uniform('logmu', -1., 1.)
    parts['logsigma'] = pymc.Uniform('logsigma', np.log(1e-4), np.log(10))

    @pymc.deterministic(trace=True)
    def sigma(logsigma = parts['logsigma']):
        return np.exp(logsigma)
    
    parts['sigma'] = sigma

    parts['fracoutliers'] = pymc.Uniform('fracoutliers', 0., 1.)

    nclusters = len(mlens)
    ml_ints = np.zeros((nclusters, nsamples))
    delta_logmls = np.zeros((nclusters, nsamples))
    outlier_ml_ints = np.zeros((nclusters, nsamples))
    outlier_delta_logmls = np.zeros((nclusters, nsamples))
    for i in range(nclusters):
        a, b = (0. - mlens[i]) /merr[i], (1e17 - mlens[i]) / merr[i]
        ml_ints[i,:] = mlens[i] + merr[i]*scipy.stats.truncnorm.rvs(a,b,size=nsamples)
        delta_logmls[i,:] = np.log(ml_ints[i,:]) - np.log(mtrue[i])

        a, b = (0. - mlens[i]) /outlierfactor*merr[i], (1e17 - mlens[i]) / outlierfactor*merr[i]
        outlier_ml_ints[i,:] = mlens[i] + outlierfactor*merr[i]*scipy.stats.truncnorm.rvs(a,b,size=nsamples)
        outlier_delta_logmls[i,:] = np.log(outlier_ml_ints[i,:]) - np.log(mtrue[i])

    

    @pymc.observed
    def data(value = 0., ml_ints = ml_ints/massnorm, delta_logmls = delta_logmls,
             outlier_ml_ints = outlier_ml_ints, outlier_delta_logmls = outlier_delta_logmls,
             logmu = parts['logmu'], sigma = parts['sigma'],
             fracoutliers = parts['fracoutliers']):

        return dlntools.outlierloglinearlike(ml_ints,
                                             delta_logmls,
                                             outlier_ml_ints,
                                             outlier_delta_logmls,
                                             logmu,
                                             sigma,
                                             fracoutliers)
    parts['data'] = data

    return parts


    

    

#######################################


def runFit(parts):

    N = pymc.NormApprox(parts)
    N.fit()
    
    return (N.mu[N.logmu], np.sqrt(N.C[N.logmu])), (N.mu[N.logsigma], np.sqrt(N.C[N.logsigma]))


#######################################

def sample(parts, outputfile, samples, adaptevery = 100, adaptafter = 100, singlecore = False):


    options = varcontainer.VarContainer()
    options.outputFile = outputfile
    options.singlecore = singlecore
    options.nsamples = samples
    options.adapt_every = adaptevery
    options.adapt_after = adaptafter
    options.restore=True

    manager = varcontainer.VarContainer()
    manager.options = options
    manager.model = pymc.Model(parts)
    
    assert(np.isfinite(manager.model.logp))

    runner = pma.MyMCRunner()

    runner.run(manager)

    runner.finalize(manager)




##############################

def memsample(parts, samples, adaptevery = 100, adaptafter = 100):

    options = varcontainer.VarContainer()
    options.singlecore = True
    options.nsamples = samples
    options.adapt_every = adaptevery
    options.adapt_after = adaptafter

    manager = varcontainer.VarContainer()
    manager.options = options
    manager.model = pymc.Model(parts)

    runner = pma.MyMCMemRunner()

    runner.run(manager)

    runner.finalize(manager)

    return manager.chain


#################
