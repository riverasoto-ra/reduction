import numpy as np

parameters = {'W51-E': {'12M':
  {'B6': {'spw5': {'mem': 128, 'ntasks': 1, 'mpi': False, 'concat': False, } },
   'B3': {'spw2': {'mem': 256, 'ntasks': 1, 'mpi': False, 'concat': True, } }
 }},
 'W43-MM3': {'12M':
  {'B3':
   {'spw0': {'mem': 128, 'ntasks': 1, 'mpi': False, 'concat': False, },
    'spw1': {'mem': 128, 'ntasks': 1, 'mpi': False, 'concat': False, } }
  },
 },
 'W43-MM1': {'12M':
  {'B3':
   {'spw1': {'mem': 128, 'ntasks': 1, 'mpi': False, 'concat': False, } }
  },
 },
}

allfields = "G008.67 G337.92 W43-MM3 G328.25 G351.77 G012.80 G327.29 W43-MM1 G010.62 W51-IRS2 W43-MM2 G333.60 G338.93 W51-E G353.41".split()
spws = {'B3': [f'spw{s}' for s in range(4)] + ['n2hp'],
        'B6': [f'spw{s}' for s in range(8)] + ['sio']}
default_parameters = {field: {array: {band: {spw:
 {'mem': 64, 'ntasks': 16, 'mpi': True, 'concat':True}
    for spw in spws[band]}
    for band in ("B3", "B6")}
    for array in ("12M", )} #"7M12M", )}
    for field in allfields}

default_parameters.update(parameters)
parameters = default_parameters


if __name__ == "__main__":
    import subprocess
    import datetime
    import os
    import json
    from astropy.io import ascii
    import sys

    with open('/orange/adamginsburg/web/secure/ALMA-IMF/tables/line_completeness_grid.json', 'r') as fh:
        imaging_status = json.load(fh)

    sacct = subprocess.check_output(['sacct',
                                   '--format=JobID,JobName%45,Account%15,QOS%17,State,Priority%8,ReqMem%8,CPUTime%15,Elapsed%15,Timelimit%15,NodeList%20'])
    tbl = ascii.read(sacct.decode().split("\n"))

    scriptpath = '/orange/adamginsburg/ALMA_IMF/reduction/reduction/slurm_scripts/'

    qos = os.getenv('QOS')
    if qos:
        account = os.environ['ACCOUNT'] = 'adamginsburg' if 'adamginsburg' in qos else 'astronomy-dept'
        if 'astronomy-dept' not in qos:
            raise ValueError(f"Invalid QOS {qos}")
    logpath = os.environ['LOGPATH']='/blue/adamginsburg/adamginsburg/slurmjobs/'


    for field, fpars in parameters.items():
        for array, arrpars in fpars.items():
            for band, bandpars in arrpars.items():
                for spw, spwpars in bandpars.items():

                    imstatus = imaging_status[field][band][spw][array]
                    if imstatus['image'] and imstatus['pbcor']:
                        #print(f"field {field} {band} {spw} {array} is done: imstatus={imstatus}")
                        continue
                    elif imstatus['WIP']:
                        #print(f"field {field} {band} {spw} {array} is in progress: imstatus={imstatus['WIP']}")
                        continue
                    else:
                        print(f"field {field} {band} {spw} {array} has not begun: imstatus={imstatus}")

                    print(f"spw={spw}, spwpars={spwpars}")
                    if 'spw' in spw:
                        fullcube = 'fullcube'
                        suffix = '_' + spw.lstrip('spw')
                    else:
                        fullcube = spw
                        suffix = ''

                    jobname = f"{field}_{band}_{fullcube}_{array}{suffix}"

                    match = tbl['JobName'] == jobname
                    if any(match):
                        states = np.unique(tbl['State'][match])
                        if 'RUNNING' in states:
                            jobid = tbl['JobID'][match & (tbl['State'] == 'RUNNING')]
                            continue
                            print(f"Skipped job {jobname} because it's running as {jobid}")
                        elif 'COMPLETED' in states:
                            jobid = tbl['JobID'][match & (tbl['State'] == 'COMPLETED')]
                            print(f"Skipped job {jobname} because it's COMPLETED as {jobid}")
                            continue
                        elif 'FAILED' in states:
                            jobid = tbl['JobID'][match & (tbl['State'] == 'FAILED')]
                            if '--redo-failed' in sys.argv:
                                print(f"Redoing job {jobname} even though it's FAILED as {jobid}")
                            else:
                                print(f"Skipped job {jobname} because it's FAILED as {jobid}")
                                continue
                        elif 'PENDING' in states:
                            jobid = tbl['JobID'][match & (tbl['State'] == 'PENDING')]
                            print(f"Skipped job {jobname} because it's PENDING as {jobid}")
                            continue
                        elif 'TIMEOUT' in states:
                            jobid = tbl['JobID'][match & (tbl['State'] == 'TIMEOUT')]
                            print(f"Restarting job {jobname} because it TIMED OUT as {jobid}")

                    # handle specific parameters
                    mem = int(spwpars["mem"])
                    os.environ['MEM'] = mem = f'{mem}gb'
                    ntasks = spwpars["ntasks"]
                    os.environ['NTASKS'] = str(ntasks)
                    os.environ['SLURM_NTASKS'] = str(ntasks)
                    os.environ['DO_NOT_CONCAT'] = str(not spwpars["concat"])
                    os.environ['EXCLUDE_7M'] = str('7M' not in array)
                    os.environ['ONLY_7M'] = str(array == '7M')
                    os.environ['BAND_TO_IMAGE'] = band
                    os.environ['BAND_NUMBERS'] = band[1]
                    os.environ['SPW_TO_IMAGE'] = spw[-1]
                    os.environ['LINE_NAME'] = spw

                    if spwpars['mpi']:
                        mpisuffix = '_mpi'
                        cpus_per_task = 1
                        os.environ['SLURM_TASKS_PER_NODE'] = str(ntasks)
                    else:
                        assert ntasks == 1
                        mpisuffix = ''
                        cpus_per_task = ntasks

                    os.environ['CPUS_PER_TASK'] = str(cpus_per_task)

                    runcmd = f'{scriptpath}/run_line_imaging_slurm{mpisuffix}.sh'

                    now = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
                    os.environ['LOGFILENAME'] = f"{logpath}/casa_log_line_{jobname}_{now}.log"


                    cmd = f'sbatch --ntasks={ntasks} --cpus-per-task={cpus_per_task} --mem={mem} --output={jobname}_%j.log --job-name={jobname} --account={account} --qos={qos} --export=ALL  {runcmd}'

                    if '--dry-run' in sys.argv:
                        print(cmd)
                    else:
                        sbatch = subprocess.check_output(cmd.split())

                        print(f"Started sbatch job with jobid={sbatch}")
