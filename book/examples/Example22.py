"""Example 22."""

from Definitions import *

# . Read the system definition.
solvent = Unpickle ( os.path.join ( scratchPath, "water216_cubicBox.pkl" ) )
solvent.Summary ( )

# . Define a normal deviate generator in a given state.
normalDeviateGenerator = NormalDeviateGenerator.WithRandomNumberGenerator ( RandomNumberGenerator.WithSeed ( 917133 ) )

# . Equilibration.
LeapFrogDynamics_SystemGeometry ( solvent                         ,
                                  logFrequency           =    500 ,
                                  normalDeviateGenerator = normalDeviateGenerator ,
                                  pressure               =    1.0 ,
                                  pressureControl        =   True ,
                                  pressureCoupling       = 2000.0 ,
                                  steps                  =   5000 ,
                                  temperature            =  300.0 ,
                                  temperatureControl     =   True ,
                                  temperatureCoupling    =    0.1 ,
                                  timeStep               =  0.001 )

# . Data-collection.
trajectory = SystemGeometryTrajectory ( os.path.join ( scratchPath, "water216_cubicBox_cpt.trj" ), solvent, mode = "w" )
LeapFrogDynamics_SystemGeometry ( solvent                      ,
                                  logFrequency        =    500 ,
                                  pressure            =    1.0 ,
                                  pressureControl     =   True ,
                                  pressureCoupling    = 2000.0 ,
                                  steps               =  10000 ,
                                  temperature         =  300.0 ,
                                  temperatureControl  =   True ,
                                  temperatureCoupling =    0.1 ,
                                  timeStep            =  0.001 ,
                                  trajectories        = [ ( trajectory, 50 ) ] )
