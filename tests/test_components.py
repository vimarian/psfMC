import numpy as np
import matplotlib.pyplot as pp
import pyfits
import os
import subprocess
from math import fsum
from scipy.ndimage import shift
from psfMC.ModelComponents import Sersic, PSF
from psfMC.array_utils import array_coords
from timeit import timeit

_sersic_ref_file = 'gfsim.fits.gz'
_psf_ref_shift = np.array((2.2, 2.7))


def test_sersic():
    if not os.path.exists(_sersic_ref_file):
        subprocess.call(['galfit', 'sim.feedme'])
    gfmodel = pyfits.getdata(_sersic_ref_file)

    gfhdr = pyfits.getheader(_sersic_ref_file)
    for key in [key for key in gfhdr if key.startswith('1_')]:
        gfhdr[key] = float(gfhdr[key].split('+/-')[0])
    r_maj = gfhdr['1_RE']
    r_min = r_maj*gfhdr['1_AR']

    mcmodel = np.zeros_like(gfmodel)
    coords = array_coords(mcmodel)
    ser = Sersic(xy=(gfhdr['1_XC']-1, gfhdr['1_YC']-1),
                 mag=gfhdr['1_MAG'], index=gfhdr['1_N'],
                 reff=r_maj, reff_b=r_min,
                 angle=gfhdr['1_PA'], angle_degrees=True)
    ser.add_to_array(mcmodel, mag_zp=gfhdr['MAGZPT'], coords=coords)

    radii = np.sqrt(ser.coordinate_sq_radii(coords))
    radii = radii.reshape(mcmodel.shape)

    sbeff = ser.sb_eff_adu(mag_zp=gfhdr['MAGZPT'])

    print 'Commanded magnitude: {:0.2f}'.format(gfhdr['1_MAG'])
    for model, name in [(gfmodel, 'Galfit'), (mcmodel, ' psfMC')]:
        inside = fsum(model[radii <= 1])
        outside = fsum(model[radii >= 1])
        totalmag = -2.5*np.log10(fsum(model.flat)) + gfhdr['MAGZPT']
        print '{}: Inside: {:0.4f} Outside: {:0.4f} Mag: {:0.2f}'.format(
            name, inside, outside, totalmag)

    abs_error = mcmodel - gfmodel
    frac_error = abs_error / gfmodel

    pp.figure(figsize=(7, 3.5))
    errs = [(abs_error, 'Absolute Error'), (frac_error, 'Fractional Error')]
    for step, (err_arr, title) in enumerate(errs):
        pp.subplot((121+step))
        pp.imshow(err_arr, interpolation='nearest', origin='lower')
        pp.colorbar()
        pp.contour(err_arr, levels=[0, ], colors='black')
        pp.contour(np.abs(frac_error), levels=[0.01, ], colors='white')
        pp.contour(radii, levels=[1, ], colors='SeaGreen')
        pp.title(title)

    pp.figtext(0.5, 1.0, r'Green: $\Sigma_e$ isophote, ' +
                         'Black: 0% error contour, ' +
                         'White: 1% error contour',
               va='top', ha='center')

    pp.show()

    def timing_check():
        return ser.add_to_array(mcmodel, mag_zp=gfhdr["MAGZPT"], coords=coords)

    print 'Timing, adding Sersic profile to 128x128 array'
    niter = 1000
    tottime = timeit(timing_check, number=niter)
    print 'Total: {:0.3g}s Each: {:0.3g}s'.format(tottime, tottime / niter)


def test_psf():
    print 'Testing PSF component fractional positioning'
    refarr = np.zeros((5, 5))
    # can't put this on the array edge because of boundary modes?
    refarr[1, 1] = 1.0
    # must reverse for scipy.ndimage.shift, since arrays are row, col indexed
    refarr = shift(refarr, _psf_ref_shift[::-1]-1, order=1)

    testarr = np.zeros((5, 5))
    psf = PSF(xy=_psf_ref_shift, mag=0)
    psf.add_to_array(testarr, mag_zp=0)

    assert np.allclose(refarr, testarr)

    mcmodel = np.zeros((128, 128))
    def timing_check():
        return psf.add_to_array(mcmodel, mag_zp=0)

    print 'Timing, adding PSF component to 128x128 array'
    niter = 1000
    tottime = timeit(timing_check, number=niter)
    print 'Total: {:0.3g}s Each: {:0.3g}s'.format(tottime, tottime / niter)

if __name__ == '__main__':
    test_psf()
    test_sersic()