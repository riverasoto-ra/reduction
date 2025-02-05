"""
This script is a work in progress as of Nov 26

It is intended to be run in `imaging_results/` and will produce statcont contfiles

It is partly a performance test - for the bigger cubes, there were sometimes memory problems

The noise estimation region and num_workers are both hard-coded and should be
customized.

We should eventually allow multi-cube combination using full statcont abilities
"""
import time
import warnings
from astropy.table import Table
from spectral_cube import SpectralCube
from astropy.io import fits
import dask

from statcont.cont_finding import c_sigmaclip_scube

import glob

import tempfile

import os

# for zarr storage
os.environ['TMPDIR'] = '/blue/adamginsburg/adamginsburg/tmp'


if __name__ == "__main__":
    # need to be in main block for dask to work
    #from dask.distributed import Client
    #if os.getenv('SLURM_MEM_PER_NODE'):
    #    memlim_total = int(os.getenv('SLURM_MEM_PER_NODE')) / 1024 # GB
    #    ntasks = int(os.getenv('SLURM_NTASKS'))
    #    memlim = memlim_total / ntasks
    #    print(f"Memory limit is {memlim} GB")
    #else:
    #    memlim = 1
    #    ntasks = 8
    #client = Client(memory_limit=f'{memlim}GB', n_workers=ntasks)
    #nworkers = len(client.scheduler_info()['workers'])
    #print(f"Client scheduler info: {client.scheduler_info()['services']}")
    #print(f"Number of workers: {nworkers}  (should be equal to ntasks={ntasks})")
    #print(f"Client scheduler info: {client.scheduler_info()}")
    #print(f"Client vers: {client.get_versions(check=True)}")
    if os.getenv('ENVIRONMENT') == 'BATCH':
        pass
    else:
        from dask.diagnostics import ProgressBar
        pbar = ProgressBar()
        pbar.register()

    nthreads = os.getenv('SLURM_NTASKS')
    if nthreads is not None:
        nthreads = int(nthreads)
        dask.config.set(scheduler='threads')
    else:
        dask.config.set(scheduler='synchronous')

    scheduler = dask.config.get('scheduler')
    print(f"Using {nthreads} threads with the {scheduler} scheduler")

    assert tempfile.gettempdir() == '/blue/adamginsburg/adamginsburg/tmp'

    redo = False

    basepath = '/orange/adamginsburg/ALMA_IMF/2017.1.01355.L/imaging_results'

    tbl = Table.read('/orange/adamginsburg/web/secure/ALMA-IMF/tables/cube_stats.ecsv')

    def get_size(start_path='.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size

    # simpler approach
    #sizes = {fn: get_size(fn) for fn in glob.glob(f"{basepath}/*_12M_spw[0-9].image")}
    filenames = [f'{basepath}/{fn}' for fn in tbl['filename']] + list(glob.glob(f"{basepath}/*_12M_spw[0-9].image")) + list(glob.glob(f"{basepath}/*_12M_sio.image"))

    # use tbl, ignore 7m12m
    sizes = {ii: get_size(fn)
             for ii, fn in enumerate(filenames)
             if '_12M_spw' in fn and os.path.exists(fn)
            } # ignore 7m12m


    for ii in sorted(sizes, key=lambda x: sizes[x]):

        fn = filenames[ii]+".pbcor"

        outfn = fn+'.statcont.cont.fits'

        if not os.path.exists(outfn) or redo:
            t0 = time.time()

            # touch the file to allow parallel runs
            with open(outfn, 'w') as fh:
                fh.write("")

            print(f"{fn}->{outfn}, size={sizes[ii]/1024**3} GB")

            target_chunk_size = int(1e5)
            print(f"Target chunk size is {target_chunk_size}")
            cube = SpectralCube.read(fn, target_chunk_size=target_chunk_size, format='casa_image')
            print(f"Minimizing {cube}")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cube = cube.minimal_subcube()
            print(cube)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with cube.use_dask_scheduler('threads', num_workers=nthreads):
                    print("Calculating noise")
                    if ii < len(tbl):
                        noise = tbl['std'].quantity[ii]
                    else:
                        noise = cube.std()

                    print("Sigma clipping")
                    result = c_sigmaclip_scube(cube, noise,
                                               verbose=True,
                                               save_to_tmp_dir=True)
                    print("Running the compute step")
                    data_to_write = result[1].compute()

                    print(f"Writing to FITS {outfn}")
                    fits.PrimaryHDU(data=data_to_write.value,
                                    header=cube[0].header).writeto(outfn,
                                                                   overwrite=True)
            print(f"{fn} -> {outfn} in {time.time()-t0}s")
        else:
            print(f"Skipped {fn}")
