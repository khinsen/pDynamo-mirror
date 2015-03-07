"""Geometry optimization test on a set of molecules.

The molecules are those that form the unofficial set used when testing
optimization algorithms in the Gaussian program. The set was kindly
provided by O. Farkas, Hungarian Academy of Sciences.
"""

# . The minimizers employed might change.

import glob, math, os.path

from pBabel           import XYZFile_ToCoordinates3, XYZFile_ToSystem
from pCore            import CPUTime, logFile, LogFileActive, TestCase, YAMLUnpickle
from pMolecule        import ElectronicState, QCModelMNDO
from pMoleculeScripts import ConjugateGradientMinimize_SystemGeometry , \
                             FIREMinimize_SystemGeometry              , \
                             LBFGSMinimize_SystemGeometry             , \
                             SteepestDescentMinimize_SystemGeometry

#===================================================================================================================================
# . Parameters.
#===================================================================================================================================
# . Limits.
_BestEnergyTolerance = 0.1
_BestTimeTolerance   = 0.01
_MaximumMoleculeSize = 60

# . Minimizers.
_Options    = { "logFrequency" : 10, "maximumIterations" : 500, "rmsGradientTolerance" : 1.5 }
_Minimizers = ( ( "Conjugate Gradient" , ConjugateGradientMinimize_SystemGeometry , _Options ) ,
                ( "FIRE"               , FIREMinimize_SystemGeometry              , _Options ) ,
                ( "L-BFGS"             , LBFGSMinimize_SystemGeometry             , _Options ) ,
                ( "Steepest Descent"   , SteepestDescentMinimize_SystemGeometry   , _Options ) )

# . Output options.
_TableEnergyWidth  = 20
_TableIntegerWidth = 10
_TableLabelWidth   = 22
_TableStarWidth    =  2
_TableStatusWidth  = 10 
_TableTimeWidth    = 20

#===================================================================================================================================
# . Class.
#===================================================================================================================================
class OptimizeGeometriesTest ( TestCase ):
    """Geometry optimize a series of molecules using different minimizers."""

    def ReportsSummary ( self, reports, log = logFile ):
        """Write out a summary of the reports."""
        if LogFileActive ( log ):
            # . Initialization.
            numberOfMinimizers = len ( _Minimizers )
            numberOfMolecules  = len ( reports     )
            totals = {}
            # . Header.
            table = log.GetTable ( columns = [ _TableLabelWidth ] + numberOfMinimizers * [ _TableEnergyWidth  , _TableStarWidth ,
                                                                                           _TableStatusWidth  , 
                                                                                           _TableIntegerWidth , _TableStarWidth ,
                                                                                           _TableTimeWidth    , _TableStarWidth ] )
            table.Start   ( )
            table.Title   ( "Minimization Results (Starred Entries are Best)" )
            table.Heading ( "Molecule" )
            tags = [ minimizer[0] for minimizer in _Minimizers ]
            tags.sort ( )
            for tag in tags: table.Heading ( tag, columnSpan = 7 )
            table.Heading ( "" )
            for tag in tags:
                table.Heading ( "Energy", columnSpan = 2 )
                table.Heading ( "Success"                )
                table.Heading ( "Calls" , columnSpan = 2 )
                table.Heading ( "Time"  , columnSpan = 2 )
                totals[tag] = { "Best Calls"    : 0   ,
                                "Best Energies" : 0   ,
                                "Best Times"    : 0   ,
                                "Calls"         : 0   ,
                                "Converged"     : 0   ,
                                "Time"          : 0.0 }
            # . Molecule results.
            labels = reports.keys ( )
            labels.sort ( )
            for label in labels:
                table.Entry ( label, alignment = "left" )
                labelReports = reports[label]
                bestCalls    = min ( [ labelReports[tag]["Function Calls"] for tag in tags ] )
                bestEnergy   = min ( [ labelReports[tag]["Function Value"] for tag in tags ] )
                bestTime     = min ( [ labelReports[tag]["CPU Time"      ] for tag in tags ] )
                for tag in tags:
                    tagReports  = labelReports[tag]
                    tagTotals   = totals      [tag]
                    calls       = tagReports["Function Calls"]
                    energy      = tagReports["Function Value"]
                    isConverged = tagReports["Converged"     ]
                    time        = tagReports["CPU Time"      ]
                    tagTotals["Calls"] += calls
                    tagTotals["Time" ] += time
                    table.Entry ( "{:20.1f}".format ( energy ) )
                    if ( math.fabs ( energy - bestEnergy ) < _BestEnergyTolerance ):
                        table.Entry ( "*" ) ; tagTotals["Best Energies"] += 1
                    else:
                        table.Entry ( "" )
                    if isConverged:
                        table.Entry ( "T" ) ; tagTotals["Converged"    ] += 1
                    else:
                        table.Entry ( "F" )
                    table.Entry ( "{:d}".format ( calls ) )
                    if calls == bestCalls:
                        table.Entry ( "*" ) ; tagTotals["Best Calls"   ] += 1
                    else:
                        table.Entry ( "" )
                    table.Entry ( "{:s}".format ( CPUTime.TimeToString ( time ) ) )
                    if ( math.fabs ( time - bestTime ) < _BestTimeTolerance ):
                        table.Entry ( "*" ) ; tagTotals["Best Times"   ] += 1
                    else:
                        table.Entry ( "" )
            # . Totals and scores.
            table.Entry ( "* Cumulative Totals *", alignment = "left" )
            for tag in tags:
                tagTotals = totals[tag]
                table.Entry ( "", columnSpan = 3   )
                table.Entry ( "{:d}".format ( tagTotals["Calls"] ) )
                table.Entry ( "" )
                table.Entry ( CPUTime.TimeToString ( tagTotals["Time"] ) )
                table.Entry ( "" )
            table.Entry ( "* Scores *", alignment = "left" )
            for tag in tags:
                tagTotals = totals[tag]
                table.Entry ( "{:d}/{:d}".format ( tagTotals["Best Energies"], numberOfMolecules ) ) ; table.Entry ( "" )
                table.Entry ( "{:d}/{:d}".format ( tagTotals["Converged"    ], numberOfMolecules ) )
                table.Entry ( "{:d}/{:d}".format ( tagTotals["Best Calls"   ], numberOfMolecules ) ) ; table.Entry ( "" )
                table.Entry ( "{:d}/{:d}".format ( tagTotals["Best Times"   ], numberOfMolecules ) ) ; table.Entry ( "" )
            table.Stop ( )

    def runTest ( self ):
        """The test."""

        # . Initialization.
        isOK = True
        log  = self.GetLog ( )

        # . Paths.
        sourcePath = os.path.join ( os.getenv ( "PDYNAMO_ROOT" ), "molecularStructures", "gaussianGeometryOptimization" )
        statesPath = os.path.join ( sourcePath, "states.yaml" )
        xyzPaths   = glob.glob ( os.path.join ( sourcePath, "xyz", "*.xyz" ) )
        xyzPaths.sort ( )

        # . Get the states.
        states = YAMLUnpickle ( statesPath )

        # . Loop over the molecules.
        reports            = {}
        numberNotConverged =  0
        for xyzPath in xyzPaths:

            # . Basic set up.
            label                    = os.path.split ( xyzPath )[1][0:-4]
            ( charge, multiplicity ) = states.get ( label, ( 0, 1 ) )
            system                   = XYZFile_ToSystem ( xyzPath )
            system.electronicState   = ElectronicState ( charge = charge, multiplicity = multiplicity )
            system.DefineQCModel ( QCModelMNDO ( "am1", isSpinRestricted = True ) )
            system.Summary ( log = log )

            # . Skip molecules that are too large.
            if len ( system.atoms ) > _MaximumMoleculeSize: continue

            # . Loop over the optimizers.
            tagReports = {}
            for ( tag, minimizer, options ) in _Minimizers:

                # . Reset the system.
                system.coordinates3 = XYZFile_ToCoordinates3 ( xyzPath )
                system.Energy ( log = log )

                # . Minimization.
                keywordArguments            = dict ( options )
                keywordArguments["log"]     = log
                cpu                         = CPUTime ( )
                tagReports[tag]             = minimizer ( system, **keywordArguments )
                tagReports[tag]["CPU Time"] = cpu.Current ( )
                if not tagReports[tag].get ( "Converged", False ): numberNotConverged += 1

            # . Save the results.
            reports[label] = tagReports

        # . Finish up.
        self.ReportsSummary ( reports, log = log )
        self.assertTrue ( numberNotConverged == 0 )

#===================================================================================================================================
# . Testing.
#===================================================================================================================================
if __name__ == "__main__":

    # . Run the test.
    test = OptimizeGeometriesTest ( )
    test.run ( )
