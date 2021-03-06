#############################################################################
#
# @file volumetest.py @version 3
# This file should be called by <jobfile.sh>
# Last modified: Feb 01, 2012 10:29:38
#
# Example usage:
#
#   import os
#   import numpy as np
#   from oppvasp.vasp.volumetest import VolumeTestCubicUnitCell
#
#   job = VolumeTestCubicUnitCell(
#       lattice_parameters = np.arange(5.2, 5.8, 0.05),
#       basedir = './',
#       workdir = os.environ['SCRATCH'],
#       vaspcmd = 'vasp.x'
#   )
#   job.start(dry_run = False, first_step = 1)
#
#############################################################################
import os,sys
import numpy as np
from job import BatchJob, BatchStep
from oppvasp import util
from oppvasp.vasp.parsers import VasprunParser

class VolumeTestCubicUnitCell(BatchJob):

    def __init__(self, lattice_parameters, **kwargs):
        """
        Create a VolumeTestCubicUnitCell object. 

        Parameters
        ----------
        lattice_parameters : array of lattice parameters to test.
           A set of POSCAR files named POSCAR.1, POSCAR.2, ... 
           will be created based on the file POSCAR with the 
           second line replaced with each of these values.

        The remaining parameters are passed over to BatchJob.
        Please see BatchJob for help on these.
        """
        BatchJob.__init__(self, **kwargs)

        self.paramName = 'VOL' # summary file header
         

        for idx,param in enumerate(lattice_parameters):
            step = VolumeTestStep(idx+1, float(param))
            step.latticeparameter = param
            for template_name in BatchStep.input_files.keys():
                # use index-less 'template' file
                step[template_name] = template_name
            self.add_step(step)

        self.print_info()

    def update_summaryfile(self, step):
        try:
            vasprun = VasprunParser(step['vasprun.xml'])
        except:
            print "BatchJob: Failed to parse '%s'. Did VASP crash?" % step['vasprun.xml']
            sys.exit(1)
        
        final_step = vasprun.ionic_steps[-1]
        toten = final_step.get_total_energy()
        final_struct = final_step.get_structure()
        shortestbond,idx1,idx2 = final_struct.get_shortest_bond()
        forces = final_struct.get_forces('d') # should use cart in final
        fx = np.sum(forces[:,0])
        fy = np.sum(forces[:,1])
        fz = np.sum(forces[:,2])
        #print ','.join([str(x) for x in forces[:,0]])
        #print forces[-1]
        drift = [fz,fy,fz]
        print "not drift:",drift

        maxforce = np.max( np.sum(forces**2,axis=1) )

        pressure = final_step.get_pressure()

        cputime,realtime = vasprun.get_time_spent()

        summaryline = "%(name)s\t%(kpoints)d\t%(shortbond).3f\t%(toten).4f\t%(cpu).0f\t%(maxforce).4f\t%(pressure).2f\t%(drift).4f" % {
            'name' : step.get_name(),
            'kpoints' : vasprun.get_num_kpoints(),
            'shortbond' : shortestbond,
            'toten' : toten,
            'cpu' : cputime,
            'maxforce' : maxforce,
            'pressure' : pressure,
            'drift' : max(drift)
            }
        sf = open(self.summaryfile,'a')
        sf.write(summaryline+"\n")
        sf.close()

class VolumeTestStep(BatchStep):
    
    def __init__(self, index, paramValue):
        BatchStep.__init__(self, index)
        self.paramValue = paramValue

    def __str__(self):
        return "a = %.3f" % (self.paramValue)
    
    def get_name(self):
        return "%.3f" % (self.paramValue)
    
    def preprocess_info(self):
        """
        This method is called from the print_info method
        """
        return "  -> Update POSCAR with new lattice parameter: %.2f\n" % self.latticeparameter

    def preprocess(self):
        """
        Updates the POSCAR file to prepare for the execution of this step 
        """
        POSCAR = open('POSCAR', 'r')
        plines = POSCAR.readlines()
        POSCAR.close()
        plines[1] = '%.4f\n' % float(self.latticeparameter)
        
        ifile = open('POSCAR', 'w')
        ifile.writelines(plines)
        ifile.close()

