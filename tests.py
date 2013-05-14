from psfMC import model_psf_mcmc
import glob, sys
import subprocess
import pymc
import matplotlib.pyplot as pp

try:
    obsfiles = glob.glob(sys.argv[1])
except IndexError:
    obsfiles = ['testdata/sci_J0005-0006.fits']
try:
    psffile = sys.argv[2]
except IndexError:
    psffile = 'testdata/sci_psf.fits'

psfIVMfile = psffile.replace('sci', 'ivm')


fit_components = [('psf', 60, 70, 60, 70, 18, 23),
                  ('sersic', 60, 70, 60, 70, 22, 27.5,
                   1.5, 8.0, 0.5, 8.0, 0.1, 1.0, 0, 360)]

for obsfile in obsfiles:
    subIVMfile = obsfile.replace('sci', 'ivm')
    dbfile = obsfile.replace('sci', 'db').replace('.fits', '.pickle')
    model_psf_mcmc(obsfile, subIVMfile, psffile, psfIVMfile,
                   fit_components=fit_components,
                   db_name=dbfile, mag_zeropoint=26.2303,
                   burn=500, iter=1000)

    db = pymc.database.pickle.load(dbfile)
    for trace_name in ('0_psf_mag', '1_sersic_mag'):
        pp.hist(db.trace(trace_name)[:], bins=20)
        pp.title(trace_name)
        pp.show()

    runok = subprocess.call(['ds9', obsfile,
                             obsfile.replace('sci', 'model'),
                             obsfile.replace('sci', 'resid')])
