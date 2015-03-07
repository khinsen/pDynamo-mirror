"""Equilibrate the solvated structure for PKA."""

import os, os.path, sys
sys.path.append ( os.path.join ( os.path.dirname ( os.path.realpath ( __file__ ) ), "..", "data" ) )

from Definitions      import outPath
from pBabel           import PDBFile_FromSystem                                                                                                                   
from pCore            import NormalDeviateGenerator, Pickle, RandomNumberGenerator, Unpickle
from pMoleculeScripts import LangevinDynamics_SystemGeometry

# . Parameters.
_Steps = 10000

# . Get the system with no fixed atoms and an appropriate NB model.
system = Unpickle ( os.path.join ( outPath, "step8_b.pkl" ) )
system.Summary ( )

# . Define a normal deviate generator in a given state.
normalDeviateGenerator = NormalDeviateGenerator.WithRandomNumberGenerator ( RandomNumberGenerator.WithSeed ( 511717 ) )

# . Dynamics.
LangevinDynamics_SystemGeometry ( system                          ,
                                  collisionFrequency     =   25.0 ,
                                  logFrequency           =    100 ,
                                  normalDeviateGenerator = normalDeviateGenerator ,
                                  steps                  = _Steps ,
                                  temperature            =  300.0 ,
                                  timeStep               =  0.001 )

# . Save the system.
Pickle ( os.path.join ( outPath, "step9.pkl" ), system )

# . Print PDB file.
PDBFile_FromSystem ( os.path.join ( outPath, "step9.pdb" ), system )
